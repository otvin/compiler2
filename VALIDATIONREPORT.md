# Compiler2 - Validation Report

At present, I have compiler2 only passes a small subset of the validation suite, so it does not make sense to create a full validation report.  However I have some notes.

### Conformance tests

#### Details of failed tests

* **TEST 6.6.6.4-3** (CONF139.pas): Variable *some* has subrange *orange..green*.  Setting *some* to *orange* and then invoking *pred(some)* triggers a *value exceeds range for subrange type* runtime error.  FreePascal does same when range checking is enabled.  The test scenario expects *pred(some)* to be *red*.
