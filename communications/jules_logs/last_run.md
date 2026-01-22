INFO:JulesBridge:Message sent to session 7991854182599200102
INFO:JulesBridge:Waiting for agent response in session 7991854182599200102...
Message sent successfully to 7991854182599200102
Traceback (most recent call last):
  File "C:\coding\economics\scripts\jules_bridge.py", line 527, in <module>
    response = bridge.wait_for_agent_response(session_id, last_act_id=last_id)
  File "C:\coding\economics\scripts\jules_bridge.py", line 239, in wait_for_agent_response
    time.sleep(3)
    ~~~~~~~~~~^^^
KeyboardInterrupt
^C