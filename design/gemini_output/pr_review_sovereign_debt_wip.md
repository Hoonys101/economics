Traceback (most recent call last):
  File "C:\coding\economics\scripts\gemini_worker.py", line 303, in main
    worker.execute(
    ~~~~~~~~~~~~~~^
        args.instruction,
        ^^^^^^^^^^^^^^^^^
    ...<2 lines>...
        output_file=getattr(args, 'output', None)
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "C:\coding\economics\scripts\gemini_worker.py", line 244, in execute
    print(f"\u2696\ufe0f Validating Protocol: '{instruction}'...")
    ~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
UnicodeEncodeError: 'cp949' codec can't encode character '\u2696' in position 0: illegal multibyte sequence

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "C:\coding\economics\scripts\gemini_worker.py", line 315, in <module>
    main()
    ~~~~^^
  File "C:\coding\economics\scripts\gemini_worker.py", line 311, in main
    print(f"\u274c Error: {e}")
    ~~~~~^^^^^^^^^^^^^^^^^^
UnicodeEncodeError: 'cp949' codec can't encode character '\u274c' in position 0: illegal multibyte sequence
