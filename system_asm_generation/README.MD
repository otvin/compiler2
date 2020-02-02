### System ASM Generation

There are system functions that the compiler needs to support, where it is easier to write the code in Pascal itself, then have the compiler generate assembly which is hand-edited, and then that assembly is used by the compiler itself.

_systemio.pas_ includes procedures that, once modified, can generate printing of values to screen in the way that is required by the ISO standard.

_stringcompare.pas_ includes a function that compares two string-types.

Both of these files include a very basic test for the Pascal itself, and rough instructions for how to create the corresponding .asm files.  Note that the asm files are checked in, so these Pascal files are only included for reference (and so I can regenerate the .asm files in the future if need be).
