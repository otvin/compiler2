# Compiler2

Goal is to build an compiler that implements a large subset of ISO-7185 Pascal.  Compiler is written in python3 in Ubuntu.  The assembly files are written in NASM format.  You must install NASM via e.g. ```sudo apt-get install nasm``` in order for the program to compile the assembly.

### Current Status

Compiler2 supports the following Pascal Language features:
* ```if - then [- else]```
* ```while - do```
* ```repeat - until```
* Math operations: addition, subtraction, multiplication, floating point/integer division, and the modulo function
    * Can mix integers and reals in a single expression e.g. adding an integer to a real
    * When Real and Integer combined in an operation, result is a Real
    * Using floating point division with divisor and dividend both integers will result in a real
    * Supports Parentheses
        * Note a quirk in the ISO 7185 BNF - to multiply -7 times -3 you need to write ```-7 * (-3)``` and put parentheses around the second factor, because you cannot have the ```*``` token be immediately followed by the ```-``` token
    * Supports following arithmetic functions required by ISO standard: 
        * ```abs()```, ```sqr()```, ```sin()```, ```cos()```, ```exp()```, ```ln()```, and ```sqrt()```
    * Supports following transfer functions required by ISO standard:
        * ```trunc()``` and ```round()``` 
    * Supports following ordinal functions required by ISO standard:
        * ```chr()```, ```ord()```, ```pred()```, and ```succ()```
* Relational operators: ```=```, ```<>```, ```<```, ```<=```, ```>```, ```>=```
  * for real, integer, and user-defined enumerated types; can compare integers to reals.
* Boolean operators: ```not```, ```and```, and ```or```
* Procedures and Functions
  *  Parameters passed by value or by reference ("variable parameters" in Pascal-speak)
  *  Functions can return integers, chars, Booleans, user-defined enumerated types, or reals
  *  Up to 8 Real parameters by value, up to a combined 6 Integer/Boolean/Character/Enumerated Type or by reference parameters
  *  Integers passed in byval to Real parameters get converted to Real
  *  Recursion
* Global and local variables
    * Signed Real variables and literals (64-bit)
    * Signed Integer variables and literals (32-bit)
    * Boolean variables and literals (8-bit)
    * Character variables and literals (8-bit)
* Type Definitions
  *  Can create a new type that is an alias for Real, Integer, Char, or Boolean, or one that is defined as one of a previously-defined alias.
  *  Can create a new user-defined enumerated type
* Global and local constants
    * Signed Real, Signed Integer, Character, or String
    * the required constants ```true```, ```false```, and ```maxint```
* Write() and Writeln() to stdout
    * each take a comma-separated list of one or more parameters, with each parameter a variable, a math expression, a numeric literal, a character literal, a string literal, or a constant.'
* Comments

 
### Commentary

At this point, Compiler2 has all features from Compiler1 except for String support.  However, the String type in the original compiler is not ISO standard, it was modeled after Turbo Pascal.

Compiler2 also has the following functionality that compiler1 did not:
* Boolean and Character types
* Constants
* REPEAT..UNTIL construct
* Ability to do relational operations comparing Integer and Real types, and relational operations involving enumerated types.
* abs(), sqr(), sin(), cos(), exp(), ln(), sqrt(), trunc(), round(), chr(), ord(), succ(), and pred()
* Boolean operators not, or, and
* Type Definitions and Enumerated Types

Compiler2 also uses the official BNF from the ISO standard, whereas Compiler1 used a BNF that I updated based on a variation I had downloaded from a random website.

The big improvement in Compiler2 is that this version has been designed like a more classic compiler.  There is a lexer, which identifies all tokens in the ISO Pascal standard.
The parser generates an Abstract Syntax Tree (AST).  The compiler then transforms the AST into Three-Address Code (TAC), which is an intermediate language.  

The TAC is then converted into ASM.  Each variable in the TAC gets its own space on the stack.  The resulting code is correct, but obviously not very efficient.  However,
there are many register-allocation algorithms that can be applied to the TAC in future versions.  With the first compiler I wrote, it got very difficult
to determine where different symbols lived in memory.  In Compiler2 everything lives on the stack.  GCC does the same thing if optimizations are all turned off; you will
notice that, for example, after a function is invoked, GCC copies all function parameters to the stack.  My opinion is that this design
has made it easier to surpass the functionality of my previous attempt. 
 
 
### To run it:

```python3 compiler.py helloworld.pas```

### Unit tests

Compiler2 currently passes 144 unit tests, including 46 of the 60 unit tests created for Compiler, plus an additional test which represented the one known bug from Compiler.  You can execute the unit test suite by running:

```python3 compiler_test.py```

Current code coverage:

| File | Coverage |
|------|---------:|
|asm_generator.py|97%|
|filelocation.py|100%|
|lexer.py|88%|
|parser.py|94%|
|pascaltypes.py|68%|
|symboltable.py|93%|
|tac_ir.py|91%|

_Code for exceptions that should never occur are excluded.  Regular compiler errors e.g. syntax errors in Pascal code are covered via "compilefail" tests.  Code written for future features, e.g. the code that handles 64-bit integers in spots, does count against code coverage, so I do not forget to add them back to the code to be tested._
 



### Bibliography

The following works are cited in various comments in the Compiler2 code:

International Organization for Standardization. (1990) Pascal (ISO standard no. 7185:1990) Retrieved from [http://www.pascal-central.com/docs/iso7185.pdf]

Cooper, Doug. Standard Pascal User Reference Manual. W.W. Norton, 1983.

Johnson, M. and Zelenski, J. "Three Address Code Examples" - handout from Stanford CS143 class, Summer 2012.  Retrieved from [https://web.stanford.edu/class/archive/cs/cs143/cs143.1128/handouts/240%20TAC%20Examples.pdf]

"Three Address Code IR" - lecture slides from Stanford CS143 class.  Retrieved from [https://web.stanford.edu/class/archive/cs/cs143/cs143.1128/lectures/13/Slides13.pdf]

"Simply FPU" by Raymond Filiatreault - documented tutorials for using the x87 floating point instructions.  Retrieved from [http://www.ray.masmcode.com/tutorial/]



### Known bugs

None.

Full README coming soon.  
