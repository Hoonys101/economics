🕵️  Reviewing Code with instruction: 'Analyze this PR.'...
📖 Attached context: C:\coding\economics\design\_archive\gemini_output\pr_diff_main.txt
🚀 [GeminiWorker] Running task with manual: git_reviewer.md
Traceback (most recent call last):
  File "C:\coding\economics\_internal\scripts\gemini_worker.py", line 521, in <module>
    main()
    ~~~~^^
  File "C:\coding\economics\_internal\scripts\gemini_worker.py", line 508, in main
    worker.execute(
    ~~~~~~~~~~~~~~^
        args.instruction,
        ^^^^^^^^^^^^^^^^^
    ...<3 lines>...
        audit_file=getattr(args, 'audit', None)
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "C:\coding\economics\_internal\scripts\gemini_worker.py", line 231, in execute
    result = self.clean_output(self.run_gemini(instruction, context_files))
                               ~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\coding\economics\_internal\scripts\gemini_worker.py", line 85, in run_gemini
    process = subprocess.run(
        cmd,
    ...<4 lines>...
        shell=True
    )
  File "C:\Users\Gram Pro\AppData\Local\Programs\Python\Python313\Lib\subprocess.py", line 556, in run
    stdout, stderr = process.communicate(input, timeout=timeout)
                     ~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Gram Pro\AppData\Local\Programs\Python\Python313\Lib\subprocess.py", line 1222, in communicate
    stdout, stderr = self._communicate(input, endtime, timeout)
                     ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Gram Pro\AppData\Local\Programs\Python\Python313\Lib\subprocess.py", line 1644, in _communicate
    self.stdout_thread.join(self._remaining_time(endtime))
                            ~~~~~~~~~~~~~~~~~~~~^^^^^^^^^
  File "C:\Users\Gram Pro\AppData\Local\Programs\Python\Python313\Lib\subprocess.py", line 1255, in _remaining_time
    def _remaining_time(self, endtime):
    
KeyboardInterrupt
^C