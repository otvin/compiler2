### System ASM Generation

There are system functions that the compiler needs to support, where it is easier to write the code in Pascal itself, then have the compiler generate assembly which is hand-edited, and then that assembly is used by the compiler itself.

_systemio.pas_ includes procedures that, once modified, can generate printing of values to screen in the way that is required by the ISO standard.
