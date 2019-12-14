# Compiler2

Goal is to eventually build a Pascal compiler.  Compiler is written in python3 in Ubuntu.  The assembly files are written in NASM format.  You must install NASM via e.g. ```sudo apt-get install nasm``` in order for the program to compile the assembly.

### Current Status

Supports global variables of type Real, Integer or Boolean.  Supports a single main code block in the program.  The code block can be a series of variable assignments or statements.  Write() and writeln() are supported, as are the IF/THEN/ELSE and WHILE..DO constructs.

Supports math expressions using addition, subtraction, multiplication, integer division, the modulo function, and floating point division.  The math expressions can be created using variables or numeric literals.  The compiler can mix integers and reals in a single expression - for example, the compiler can add an integer to a real.  Using floating point division with the divisor and dividend both integers will result in a real.  Also supports parentheses.

Supports relational operators equal, not equal, less than, less than or equal to, greater than, and greater than or equal to.  Can compare Booleans to Booleans, Integers to Integers, Reals to Reals, or Integers to Reals.

Write() and writeln() each take a comma-separated list of one or more parameters, with each parameter a variable, a math expression, a numeric literal, a string literal, or the boolean constants 'true' and 'false.'

 
### Commentary

Compiler2 is less functional than compiler1 at this point.  However, this version has been designed like a more classic compiler.  There is a lexer, which identifies all tokens in the ISO Pascal standard.
The parser generates an Abstract Syntax Tree (AST).  The compiler then transforms the AST into Three-Address Code (TAC), which is an intermediate language.  

The TAC is then converted into ASM.  Each variable in the TAC gets its own space on the stack.  The resulting code is correct, but obviously not very efficient.  However,
there are many register-allocation algorithms that can be applied to the TAC in future versions.  With the first compiler I wrote, it got very difficult
to determine where different symbols lived in memory.  In Compiler2 everything lives on the stack.  GCC does the same thing if optimizations are all turned off; you will
notice that, for example, after a function is invoked, GCC copies all function parameters to the stack.  My opinion is that this design
will make it easier to surpass the functionality of my previous attempt. 
 
 
### To run it:

```python3 compiler.py helloworld.pas```

### Unit tests

Compiler2 currently passes 20 of the 60 unit tests created for Compiler, plus an additional 17 tests unique to Compiler2.  You can execute the working
bits of the unit test suite by running:

```python3 compiler_test.py```

Current code coverage:

| File | Coverage |
|------|---------:|
|asm_generator.py|96%|
|filelocation.py|100%|
|lexer.py|86%|
|parser.py|84%|
|pascaltypes.py|76%|
|symboltable.py|81%|
|tac_ir.py|91%|

_Code for exceptions that should never occur are excluded.  Regular compiler errors e.g. syntax errors in Pascal code are covered via "compilefail" tests.  Code written for future features, e.g. the code that handles 64-bit integers in spots, does count against code coverage, so I do not forget to remove the "no cover" pragma later_
 



### Bibliography

The following works are cited in various comments in the Compiler2 code:

International Organization for Standardization. (1990) Pascal (ISO standard no. 7185:1990) Retrieved from [http://www.pascal-central.com/docs/iso7185.pdf]

Cooper, Doug. Standard Pascal User Reference Manual. W.W. Norton, 1983.

Johnson, M. and Zelenski, J. "Three Address Code Examples" - handout from Stanford CS143 class, Summer 2012.  Retrieved from [https://web.stanford.edu/class/archive/cs/cs143/cs143.1128/handouts/240%20TAC%20Examples.pdf]

"Three Address Code IR" - lecture slides from Stanford CS143 class.  Retrieved from [https://web.stanford.edu/class/archive/cs/cs143/cs143.1128/lectures/13/Slides13.pdf]





### Known bugs

None.

Full README coming soon.  
