# Compiler2

Goal is to build an compiler that implements a large subset of ISO-7185 Pascal.  Compiler is written in python3 running on Ubuntu.  The assembly files are written in NASM format.  You must install NASM via e.g. ```sudo apt-get install nasm``` in order for Compiler2 to compile the assembly.

### Current Status

Compiler2 supports the following Pascal Language features:
* ```if - then [- else]```
* ```while - do```
* ```repeat - until```
* ```for - to/downto - do```
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
    * Supports following boolean function reuqired by ISO standard:
        * ```odd()``` 
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
    * Arrays (including string-types)
* Type Definitions
  *  Can create a new type that is an alias for Real, Integer, Char, or Boolean, or one that is defined as one of a previously-defined alias.
  *  Can create a new user-defined enumerated type
  *  Can create a new type that is a subrange of an Integer, Char, Boolean, or Enumerated type
  *  Can create an array type with arbitrary number of dimensions, using any ordinal or subrange as the index
        * Note the keyword "packed" is parsed, but ignored, as only booleans and enumerated types are not already stored packed.
        * Per the ISO standard, an array of 2 or more chars that is defined "packed" will be treated as a string-type.  
  *  If create a new subrange or enumerated type when declaring a variable, the type will be created anonymously (unnamed)
* Global and local constants
    * Signed Real, Signed Integer, Character, or String
    * the required constants ```true```, ```false```, and ```maxint```
* Output Files (limited)
    * Can write to stdout.  Can also write to a text file, by naming a variable in the program parameter list, declaring a variable in global scope with same name and type *text*, and then passing the name of the file in via a command-line argument.  (ISO 7185 Pascal has very limited support for files written permanently to disk)
    * Write() and Writeln() supported.
    * each take a comma-separated list of one or more parameters, with each parameter a variable, a math expression, a numeric literal, a character literal, a string literal, an array that is a string-type, or a constant.
    * Rewrite() supported for output text files.
* Comments

 
### Commentary

At this point, Compiler2 has all features from Compiler1 except for the non-standard "Concat()" function from Compiler1.  However, the String type in the original compiler is not ISO standard, it was modeled after Turbo Pascal, and Concat() would not work as a built-in in Compiler2.  

Compiler2 also has the following functionality that compiler1 did not:
* Boolean and Character types
* Constants
* REPEAT..UNTIL construct
* FOR loops
* Ability to do relational operations comparing Integer and Real types, and relational operations involving enumerated types.
* abs(), sqr(), sin(), cos(), exp(), ln(), sqrt(), trunc(), round(), chr(), ord(), succ(), pred(), and odd()
* Boolean operators not, or, and
* Writing to Text Files in addition to stdout
* Type Definitions, including Subrange Types, Enumerated Types, and arrays.

Compiler2 also uses the official BNF from the ISO standard, whereas Compiler1 used a BNF that I updated based on a variation I had downloaded from a random website.

The big improvement in Compiler2 is that this version has been designed like a more classic compiler.  There is a lexer, which identifies all tokens in the ISO Pascal standard.
The parser generates an Abstract Syntax Tree (AST).  The compiler then transforms the AST into Three-Address Code (TAC), which is an intermediate language.  

The TAC is then converted into ASM.  Each variable in the TAC gets its own space on the stack.  The resulting code is correct, but obviously not very efficient.  However,
there are many register-allocation algorithms that can be applied to the TAC in future versions.  With the first compiler I wrote, it got very difficult
to determine where different symbols lived in memory.  In Compiler2 everything lives on the stack.  GCC does the same thing if optimizations are all turned off; you will
notice that, for example, after a function is invoked, GCC copies all function parameters to the stack.  My opinion is that this design
has made it easier to surpass the functionality of my previous attempt. 

One of the cool things that I have done is used the compiler to generate assembly code for functions that are easy to write in Pascal but hard to write by hand in assembly.  One is code that prints a string-type array to screen, and another compares two strings lexicographically.  I have committed both the Pascal files and the resulting .asm files.  
 
 
### To run it:

```python3 compiler.py helloworld.pas```

### Unit tests

Compiler2 currently passes 242 unit tests, including the 48 (of 60) unit tests created for Compiler which did not use Concat() and an additional test which represented the one known bug from Compiler.  You can execute the unit test suite by running:

```python3 compiler_test.py```

Current code coverage:

| File | Coverage |
|------|---------:|
|asm_generator.py|98%|
|editor_settings.py|100%|
|filelocation.py|100%|
|lexer.py|88%|
|parser.py|94%|
|pascaltypes.py|89%|
|symboltable.py|91%|
|tac_ir.py|97%|

_Code for exceptions that should never occur are excluded, as is code that only prints text for debugging purposes.  Regular compiler errors e.g. syntax errors in Pascal code are covered via "compilefail" tests.  Code written for future features, e.g. the code that handles 64-bit integers in spots, does count against code coverage, so I do not forget to add them back to the code to be tested._
 

### BSI Validation Suite

Cloned from: https://github.com/pascal-validation/validation-suite. More details may be found [here](tests/BSI-validation-suite/README.md).

Compiler2 currently passes 80 of 221 "conform" tests from the BSI suite.  You can execute the suite by running:

```python3 validation_test.py```


### Bibliography

The following works are cited in various comments in the Compiler2 code:

International Organization for Standardization. (1990) Pascal ([ISO standard no. 7185:1990](docs/iso7185.pdf))

Cooper, Doug. Standard Pascal User Reference Manual. W.W. Norton, 1983.

Johnson, M. and Zelenski, J. "Three Address Code Examples" - handout from Stanford CS143 class, Summer 2012.  Retrieved from [https://web.stanford.edu/class/archive/cs/cs143/cs143.1128/handouts/240%20TAC%20Examples.pdf]

"Three Address Code IR" - lecture slides from Stanford CS143 class.  Retrieved from [https://web.stanford.edu/class/archive/cs/cs143/cs143.1128/lectures/13/Slides13.pdf]

"Simply FPU" by Raymond Filiatreault - documented tutorials for using the x87 floating point instructions.  Retrieved from [http://www.ray.masmcode.com/tutorial/]



### Known bugs

None


### ISO Standard Errors
Section 3.1 of the ISO Standard defines an Error as "A violation by a program of the requirements of this International Standard that a processor is permitted to leave undetected."  Section 5.1(f) of the standard says that, for each error, the processor has to report whether the error is detected at compile-time, detected at run-time, or not detected at all.  While compiler2 is nowhere near an ISO-compatible processor, it does detect many of the errors from the standard.  These are documented in the table below.

There are 60 total errors in the ISO standard.  Compiler2 handles 15 of them, has code to handle 2 others (but that code is not invoked yet), and partially handles 1 more.  The remaining errors apply to not-yet-implemented language features or are not detected.

| Error | Ref. Section|Description| How Handled|
|------|---------|---------|-------------|
|D.1|6.5.3.2|For an indexed-variable closest-containing a single index-expression, it is an error if the value of the index-expression is not assignment-compatible with the index-type of the array-type.|Detected at compile-time|
|D.7|6.6.3.2|It is an error if the value of each corresponding actual value parameter is not assignment-compatible with the type possessed by the formal-parameter.|Detected at compile-time|
|D.9|6.6.5.2|It is an error if the file mode is not Generation immediately prior to any use of *put*, *write*, *writeln*, or *page*.|Detected at runtime|
|D.10|6.6.5.2|It is an error if the file is undefined immediately prior to any use of  *put*, *write*, *writeln*, or *page*.|Detected at runtime|
|D.14|6.6.5.2|It is an error if the file mode is not Inspection immediately prior to any use of *get* or *read*.|Code to detect at runtime is built, but we do not support *get* or read* yet.|
|D.15|6.6.5.2|It is an error if the file is undefined immediately prior to any use of *get* or *read*.|Code to detect at runtime is built, but we do not support *get* or read* yet.|
|D.33|6.6.6.2|For ln(x), it is an error if x is not greater than zero.|Detected at runtime|
|D.34|6.6.6.2|For sqrt(x), it is an error if x is negative.|Detected at runtime|
|D.37|6.6.6.3|For chr(x), the function returns a result of char-type that is the value whose ordinal number is equal to the value of the expression x if such a character value exists.  It is an error if such a character value does not exist.|Detected at runtime|
|D.38|6.6.6.4|For succ(x), the function yields a value whose ordinal number is one greater than that of x, if such a value exists.  It is an error if such a value does not exist.|Detected at runtime|
|D.39|6.6.6.4|For pred(x), the function yields a value whose ordinal number is one less than that of x, if such a value exists.  It is an error if such a value does not exist.|Detected at runtime|
|D.44|6.7.2.2|A term of the form x/y is an error if y is zero.|Detected at runtime|
|D.45|6.7.2.2|A term of the form i div j is an error if j is zero.|Detected at runtime|
|D.46|6.7.2.2|A term of the form i mod j is an error if j is zero or negative.|Detected at runtime|
|D.48|6.7.3|It is an error if the result of an activation of a function is undefined upon completion of the algorithm of the activation|Partially Detected at Compile-time. All functions must contain at least one assignment to the return value, but there is no check to see that it executes.|
|D.49|6.8.2.2|For an assignment-statement, it is an error if the expression is of an ordinal-type whose value is not assignment-compatible with the type possessed by the variable or function identifier|Detected at compile-time|
|D.52|6.8.3.9|For a for-statement, it is an error if the value of the initial-value is not assignment-compatible with the type possessed by the control-variable if the statement of the for-statement is executed|Detected at runtime, but reported as a generic value exceeds range for subrange, not D.52 specifically|
|D.53|6.8.3.9|For a for-statement, it is an error if the value of the final-value is not assignment-compatible with the type possessed by the control-variable if the statement of the for-statement is executed.|Detected at runtime, but reported as a generic value exceeds range for subrange, not D.53 specifically|



