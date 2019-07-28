# compiler2

Goal is to eventually build a Pascal compiler.  Compiler is written in python3 in Ubuntu.  The assembly files are written in NASM format.  You must install NASM via e.g. ```sudo apt-get install nasm``` in order for the program to compile the assembly.

### Current Status

Supports a series of write() or writeln() calls, each with one or more comma-separated parameters.  Each parameter must be a math expression or a string literal.
 The math expressions can be integer or real or a combination - for example, the compiler can add an integer to a real.  Addition, subraction, multiplication, and parentheses are supported.  
 
### Commentary

Compiler2 is less functional than compiler1 at this point.  However, this version has been designed like a more classic compiler.  There is a lexer, which identifies all tokens in the ISO Pascal standard.
The parser generates an Abstract Syntax Tree (AST).  The compiler then transforms the AST into Three-Address Code (TAC), which is an intermediate language.  
The TAC is then converted into ASM.  Each variable in the TAC gets its own space on the stack.  The resulting code is correct, but obviously not very efficient.  However,
there are many register-allocation algorithms that can be applied to the TAC in future versions.  With the first compiler I wrote, it got very difficult
to determine where different symbols lived in memory.  In Compiler2 everything lives on the stack.  GCC does the same thing if optimizations are all turned off; you will
notice that, for example, after a function is invoked, all parameters to the function are copied to the stack.  My opinion is that this design
will make it easier to surpass the functionality of my previous attempt. 
 
 
### To run it:

```python3 compiler.py helloworld.pas```

### Unit tests

Compiler2 currently passes 10 of the 60 unit tests created for Compiler.  You can execute the working
bits of the unit test suite by running:

```python3 compiler_test.py```

Full README coming soon.  
