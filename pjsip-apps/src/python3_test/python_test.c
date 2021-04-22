// PythonIntegration.cpp : This file contains the 'main' function. Program execution begins and ends there.
//
#include <Windows.h>

#ifdef _DEBUG
#define _DEBUG_WAS_DEFINED
#undef _DEBUG
#endif
#define PY_SSIZE_T_CLEAN
#include <Python.h>
#ifdef _DEBUG_WAS_DEFINED
#define _DEBUG
#undef _DEBUG_WAS_DEFINED
#endif

int main(int argc, char* argv[])
{
    wchar_t* program = Py_DecodeLocale(argv[0], NULL);
    if (program == NULL) {
        fprintf(stderr, "Fatal error: cannot decode argv[0]\n");
        exit(1);
    }
    Py_SetProgramName(program);  /* optional but recommended */
    Py_Initialize();
    //PyObject* g = PyDict_New(); //global and locals
    //PyObject* res = PyRun_String("import _pjsua", Py_file_input, g, g);
    //Py_XDECREF(g);
    //Py_XDECREF(res);

    const char* filename = "../src/python3/samples/test_sua.py";
    FILE* fp = _Py_fopen(filename, "r");
    if(fp)
        PyRun_AnyFile(fp, filename);


    if (Py_FinalizeEx() < 0) {
        exit(120);
    }
    PyMem_RawFree(program);
    return 0;
}
