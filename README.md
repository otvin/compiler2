# Compiler2

Goal is to build an compiler that implements a large subset of ISO-7185 Pascal.  Compiler is written in python3 in Ubuntu.  The assembly files are written in NASM format.  You must install NASM via e.g. ```sudo apt-get install nasm``` in order for the program to compile the assembly.

### Current Status

Compiler2 supports the following Pascal Language features:
* if - then [- else]
* while - do
* repeat - until
* Math operations: addition, subtraction, multiplication, floating point/integer division, and the modulo function
    * Can mix integers and reals in a single expression e.g. adding an integer to a real
    * When Real and Integer combined in an operation, result is a Real
    * Using floating point division with divisor and dividend both integers will result in a real
    * Supports Parentheses
        * Note a quirk in the ISO 7185 BNF - to multiply -7 times -3 you need to write ```-7 * (-3)``` and put parentheses around the second factor, because you cannot have the ```*``` token be immediately followed by the ```-``` token
    * Supports following function required by ISO standard: sqrt()
* Logical operators: equal to, not equal, less than, less than or equal, greater than, greater than or equal
  * both Real and Integer; can compare integers to reals.
* Procedures and Functions
  *  Parameters passed by value or by reference ("variable parameters" in Pascal-speak)
  *  Functions can return integers, Booleans, or reals
  *  Up to 8 Real parameters by value, up to a combined 6 Integer/String or by reference parameters
  *  Integers passed in byval to Real parameters get converted to Real
  *  Recursion
* Global and local variables
    * Signed Real variables and literals (64-bit)
    * Signed Integer variables and literals (32-bit)
    * Boolean variables and literals (8-bit)
* Write() and Writeln() to stdout
    * each take a comma-separated list of one or more parameters, with each parameter a variable, a math expression, a numeric literal, a string literal, or the boolean constants 'true' and 'false.'
* Comments

 
### Commentary

At this point, Compiler2 has all features from Compiler1 except for String support.

Compiler2 also has the following functionality that compiler1 did not:
* Boolean type
* REPEAT..UNTIL construct
* Ability to do relational operations comparing Integer and Real types
* sqrt() function

Compiler2 also uses the official BNF from the ISO standard, whereas Compiler1 used a BNF that I updated based on a variation I had downloaded from a random website.

The big improvement in Compiler2 is that this version has been designed like a more classic compiler.  There is a lexer, which identifies all tokens in the ISO Pascal standard.
The parser generates an Abstract Syntax Tree (AST).  The compiler then transforms the AST into Three-Address Code (TAC), which is an intermediate language.  

The TAC is then converted into ASM.  Each variable in the TAC gets its own space on the stack.  The resulting code is correct, but obviously not very efficient.  However,
there are many register-allocation algorithms that can be applied to the TAC in future versions.  With the first compiler I wrote, it got very difficult
to determine where different symbols lived in memory.  In Compiler2 everything lives on the stack.  GCC does the same thing if optimizations are all turned off; you will
notice that, for example, after a function is invoked, GCC copies all function parameters to the stack.  My opinion is that this design
will make it easier to surpass the functionality of my previous attempt. 
 
 
### To run it:

```python3 compiler.py helloworld.pas```

### Unit tests

Compiler2 currently passes 46 of the 60 unit tests created for Compiler, plus an additional 53
 tests unique to Compiler2.  You can execute the working
bits of the unit test suite by running:

```python3 compiler_test.py```

Current code coverage:

| File | Coverage |
|------|---------:|
|asm_generator.py|97%|
|filelocation.py|100%|
|lexer.py|88%|
|parser.py|92%|
|pascaltypes.py|76%|
|symboltable.py|92%|
|tac_ir.py|92%|

_Code for exceptions that should never occur are excluded.  Regular compiler errors e.g. syntax errors in Pascal code are covered via "compilefail" tests.  Code written for future features, e.g. the code that handles 64-bit integers in spots, does count against code coverage, so I do not forget to add them back to the code to be tested._
 



### Bibliography

The following works are cited in various comments in the Compiler2 code:

International Organization for Standardization. (1990) Pascal (ISO standard no. 7185:1990) Retrieved from [http://www.pascal-central.com/docs/iso7185.pdf]

Cooper, Doug. Standard Pascal User Reference Manual. W.W. Norton, 1983.

Johnson, M. and Zelenski, J. "Three Address Code Examples" - handout from Stanford CS143 class, Summer 2012.  Retrieved from [https://web.stanford.edu/class/archive/cs/cs143/cs143.1128/handouts/240%20TAC%20Examples.pdf]

"Three Address Code IR" - lecture slides from Stanford CS143 class.  Retrieved from [https://web.stanford.edu/class/archive/cs/cs143/cs143.1128/lectures/13/Slides13.pdf]





### Known bugs

None.

Full README coming soon.  
