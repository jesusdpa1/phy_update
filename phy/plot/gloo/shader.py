# -----------------------------------------------------------------------------
# Copyright (c) 2009-2016 Nicolas P. Rougier. All rights reserved.
# Distributed under the (new) BSD License.
# -----------------------------------------------------------------------------
"""
A Shader is a user-defined program designed to run on some stage of a
graphics processor. Its purpose is to execute one of the programmable stages of
the rendering pipeline.

Read more on shaders on `OpenGL Wiki <https://www.opengl.org/wiki/Shader>`_

**Example usage**

  .. code:: python

     vertex = '''
         attribute vec2 position;
         void main (void)
         {
             gl_Position = vec4(0.85*position, 0.0, 1.0);
         } '''
     fragment = '''
         void main(void)
         {
             gl_FragColor = vec4(1.0,1.0,0.0,1.0);
         } '''

     quad = gloo.Program(vertex, fragment, count=4)
     quad['position'] = [(-1,-1), (-1,+1), (+1,-1), (+1,+1)]
"""

import logging
import os.path
import re

from . import gl
from .globject import GLObject
from .parser import get_attributes, get_hooks, get_uniforms, preprocess, remove_comments
from .snippet import Snippet

log = logging.getLogger(__name__)


# ------------------------------------------------------------ Shader class ---
class Shader(GLObject):
    """
    Abstract shader class.

    :param gl.GLEnum target:

       * gl.GL_VERTEX_SHADER
       * gl.GL_FRAGMENT_SHADER
       * gl.GL_GEOMETRY_SHADER

    :param str code: Shader code or a filename containing shader code

    .. note::

       If the shader code is actually a filename, the filename must be prefixed
       with ``file:``. Note that you can also get shader code from the library
       module.
    """

    _gtypes = {
        'float': gl.GL_FLOAT,
        'vec2': gl.GL_FLOAT_VEC2,
        'vec3': gl.GL_FLOAT_VEC3,
        'vec4': gl.GL_FLOAT_VEC4,
        'int': gl.GL_INT,
        'ivec2': gl.GL_INT_VEC2,
        'ivec3': gl.GL_INT_VEC3,
        'ivec4': gl.GL_INT_VEC4,
        'bool': gl.GL_BOOL,
        'bvec2': gl.GL_BOOL_VEC2,
        'bvec3': gl.GL_BOOL_VEC3,
        'bvec4': gl.GL_BOOL_VEC4,
        'mat2': gl.GL_FLOAT_MAT2,
        'mat3': gl.GL_FLOAT_MAT3,
        'mat4': gl.GL_FLOAT_MAT4,
        'sampler1D': gl.GL_SAMPLER_1D,
        'sampler2D': gl.GL_SAMPLER_2D,
        'samplerCube': gl.GL_SAMPLER_CUBE,
    }

    def __init__(self, target, code, version='120'):
        """
        Initialize the shader.
        """

        GLObject.__init__(self)
        self._target = target
        self._snippets = {}
        self._version = version

        if os.path.isfile(code):
            with open(str(code)) as file:
                self._code = preprocess(file.read())
                self._source = os.path.basename(code)
        else:
            self._code = preprocess(str(code))
            self._source = '<string>'

        self._hooked = self._code
        self._need_update = True
        self._program = None

    def __setitem__(self, name, snippet):
        """
        Set a snippet on the given hook in the source code.
        """

        self._snippets[name] = snippet

    def _replace_hooks(self, name, snippet):
        # re_hook = r"(?P<hook>%s)(\.(?P<subhook>\w+))?" % name
        re_hook = rf'(?P<hook>{name})(\.(?P<subhook>[\.\w\!]+))?'
        re_args = r'(\((?P<args>[^<>]+)\))?'
        # re_hooks = re.compile("\<" + re_hook + re_args + "\>", re.VERBOSE)
        pattern = r'\<' + re_hook + re_args + r'\>'

        # snippet is not a Snippet (it should be a string)
        if not isinstance(snippet, Snippet):

            def replace(match):
                # hook = match.group('hook')
                subhook = match.group('subhook')
                if subhook:
                    return f'{snippet}.{subhook}'
                return snippet

            self._hooked = re.sub(pattern, replace, self._hooked)
            return

        # Store snippet code for later inclusion
        # self._snippets.append(snippet)

        # Replace expression of type <hook.subhook(args)>
        def replace_with_args(match):
            # hook = match.group('hook')
            subhook = match.group('subhook')
            # args = match.group('args')

            if subhook and '.' in subhook:
                s = snippet
                for item in subhook.split('.')[:-1]:
                    if isinstance(s[item], Snippet):
                        s = s[item]
                subhook = subhook.split('.')[-1]

                # If the last snippet name endswith "!" this means to call
                # the snippet with given arguments and not the ones stored.
                # If S = A(B(C))("t"):
                #   <S>     -> A(B(C("t")))
                #   <S!>(t) -> A("t")
                override = False
                if subhook[-1] == '!':
                    override = True
                    subhook = subhook[:-1]

                # Do we have a class alias ? We don't return it yet since we
                # need its translation from the symbol table
                if subhook in s.aliases.keys():
                    subhook = s.aliases[subhook]
                # If subhook is a variable (uniform/attribute/varying)
                if subhook in s.globals:
                    return s.globals[subhook]
                return s.mangled_call(subhook, match.group('args'), override=override)

            # If subhook is a variable (uniform/attribute/varying)
            if subhook in snippet.globals:
                return snippet.globals[subhook]
            return snippet.mangled_call(subhook, match.group('args'))

        self._hooked = re.sub(pattern, replace_with_args, self._hooked)

    def reset(self):
        """Reset shader snippets"""

        self._snippets = {}

    @property
    def code(self):
        """Shader source code (built from original and snippet codes)"""

        # Last minute hook settings
        self._hooked = self._code
        for name, snippet in self._snippets.items():
            self._replace_hooks(name, snippet)

        snippet_code = '// --- Snippets code : start --- //\n'
        deps = []
        for snippet in self._snippets.values():
            if isinstance(snippet, Snippet):
                deps.extend(snippet.dependencies)
        for snippet in list(set(deps)):
            snippet_code += snippet.mangled_code()
        snippet_code += '// --- Snippets code : end --- //\n'
        return snippet_code + self._hooked

    def _create(self):
        """Create the shader"""

        log.log(5, 'GPU: Creating shader')

        # Check if we have something to compile
        if not self.code:
            raise RuntimeError('No code has been given')

        # Check that shader object has been created
        if self._handle <= 0:
            self._handle = gl.glCreateShader(self._target)
            if self._handle <= 0:
                raise RuntimeError('Cannot create shader object')

    def _update(self):
        """Compile the source and checks everything's ok"""

        log.log(5, 'GPU: Compiling shader')

        if len(self.hooks):
            hooks = [name for name, snippet in self.hooks]
            error = f'Shader has pending hooks ({hooks}), cannot compile'
            raise RuntimeError(error)

        # Set shader version
        code = f'#version {self._version}\n{self.code}'
        gl.glShaderSource(self._handle, code)

        # Actual compilation
        gl.glCompileShader(self._handle)
        status = gl.glGetShaderiv(self._handle, gl.GL_COMPILE_STATUS)
        if not status:
            error = gl.glGetShaderInfoLog(self._handle).decode()
            parsed_errors = self._parse_error(error)
            for lineno, mesg in parsed_errors:
                self._print_error(mesg, lineno - 1)
            raise RuntimeError('Shader compilation error')

    def _delete(self):
        """Delete shader from GPU memory (if it was present)."""

        gl.glDeleteShader(self._handle)

    _ERROR_RE = [
        # Nvidia
        # 0(7): error C1008: undefined variable "MV"
        # 0(2) : error C0118: macros prefixed with '__' are reserved
        re.compile(
            r'^\s*(\d+)\((?P<line_no>\d+)\)\s*:\s(?P<error_msg>.*)', re.MULTILINE
        ),
        # ATI / Intel
        # ERROR: 0:131: '{' : syntax error parse error
        re.compile(
            r'^\s*ERROR:\s(\d+):(?P<line_no>\d+):\s(?P<error_msg>.*)', re.MULTILINE
        ),
        # Nouveau
        # 0:28(16): error: syntax error, unexpected ')', expecting '('
        re.compile(
            r'^\s*(\d+):(?P<line_no>\d+)\((\d+)\):\s(?P<error_msg>.*)', re.MULTILINE
        ),
    ]

    def _parse_error(self, error):
        """
        Parses a single GLSL error and extracts the line number and error
        description.

        Parameters
        ----------
        error : str
            An error string as returned by the compilation process
        """
        for error_re in self._ERROR_RE:
            matches = list(error_re.finditer(error))
            if matches:
                errors = [
                    (int(m.group('line_no')), m.group('error_msg')) for m in matches
                ]
                return sorted(errors, key=lambda elem: elem[0])
        else:
            raise ValueError(f'Unknown GLSL error format:\n{error}\n')

    def _print_error(self, error, lineno):
        """
        Print error and show the faulty line + some context

        Parameters
        ----------
        error : str
            An error string as returned byt the compilation process

        lineno: int
            Line where error occurs
        """
        lines = self.code.split('\n')
        start = max(0, lineno - 3)
        end = min(len(lines), lineno + 3)

        print(f'Error in {repr(self)}')
        print(f' -> {error}')
        print()
        if start > 0:
            print(' ...')
        for i, line in enumerate(lines[start:end]):
            if (i + start) == lineno:
                print(f' {i + start:03d} {line}')
            else:
                if len(line):
                    print(f' {i + start:03d} {line}')
        if end < len(lines):
            print(' ...')
        print()

    @property
    def hooks(self):
        """Shader hooks (place where snippets can be inserted)"""

        # We get hooks from the original code, not the hooked one
        code = remove_comments(self._hooked)
        return get_hooks(code)

    @property
    def uniforms(self):
        """Shader uniforms obtained from source code"""

        code = remove_comments(self.code)
        gtypes = Shader._gtypes
        return [(n, gtypes[t]) for (n, t) in get_uniforms(code)]

    @property
    def attributes(self):
        """Shader attributes obtained from source code"""

        code = remove_comments(self.code)
        gtypes = Shader._gtypes
        return [(n, gtypes[t]) for (n, t) in get_attributes(code)]


# ------------------------------------------------------ VertexShader class ---
class VertexShader(Shader):
    """Vertex shader class"""

    def __init__(self, code=None, version='120'):
        Shader.__init__(self, gl.GL_VERTEX_SHADER, code, version)

    @property
    def code(self):
        code = super().code
        code = f'#define _GLUMPY__VERTEX_SHADER__\n{code}'
        return code

    def __repr__(self):
        return f'Vertex shader {self._id} ({self._source})'


class FragmentShader(Shader):
    """Fragment shader class"""

    def __init__(self, code=None, version='120'):
        Shader.__init__(self, gl.GL_FRAGMENT_SHADER, code, version)

    @property
    def code(self):
        code = super().code
        code = f'#define _GLUMPY__FRAGMENT_SHADER__\n{code}'
        return code

    def __repr__(self):
        return f'Fragment shader {self._id} ({self._source})'


class GeometryShader(Shader):
    """Geometry shader class.

    :param str code: Shader code or a filename containing shader code
    :param int vertices_out: Number of output vertices
    :param gl.GLEnum input_type:

       * GL_POINTS
       * GL_LINES​, GL_LINE_STRIP​, GL_LINE_LIST
       * GL_LINES_ADJACENCY​, GL_LINE_STRIP_ADJACENCY
       * GL_TRIANGLES​, GL_TRIANGLE_STRIP​, GL_TRIANGLE_FAN
       * GL_TRIANGLES_ADJACENCY​, GL_TRIANGLE_STRIP_ADJACENCY

    :param gl.GLEnum output_type:

       * GL_POINTS, GL_LINES​, GL_LINE_STRIP
       * GL_TRIANGLES​, GL_TRIANGLE_STRIP​, GL_TRIANGLE_FAN
    """

    def __init__(
        self,
        code=None,
        vertices_out=None,
        input_type=None,
        output_type=None,
        version='120',
    ):
        Shader.__init__(self, gl.GL_GEOMETRY_SHADER_EXT, code, version)

        self._vertices_out = vertices_out

        # GL_POINTS
        # GL_LINES​, GL_LINE_STRIP​, GL_LINE_LIST
        # GL_LINES_ADJACENCY​, GL_LINE_STRIP_ADJACENCY
        # GL_TRIANGLES​, GL_TRIANGLE_STRIP​, GL_TRIANGLE_FAN
        # GL_TRIANGLES_ADJACENCY​, GL_TRIANGLE_STRIP_ADJACENCY
        self._input_type = input_type

        # GL_POINTS, GL_LINES​, GL_LINE_STRIP
        # GL_TRIANGLES​, GL_TRIANGLE_STRIP​, GL_TRIANGLE_FAN
        self._output_type = output_type

    @property
    def vertices_out(self):
        return self._vertices_out

    @vertices_out.setter
    def vertices_out(self, value):
        self._vertices_out = value

    @property
    def input_type(self):
        """ """
        return self._input_type

    @input_type.setter
    def input_type(self, value):
        self._input_type = value

    @property
    def output_type(self):
        return self._output_type

    @output_type.setter
    def output_type(self, value):
        self._output_type = value

    def __repr__(self):
        return f'Geometry shader {self._id} ({self._source})'
