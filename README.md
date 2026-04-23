# Distributed Chat Room System

A 3-node distributed system implementing a chat room with Distributed Mutual Exclusion (DME).

## Architecture

```
+----------------+     +----------------+
|    Node 1      |     |    Node 2      |
|  (Chat Client) |<--->|  (Chat Client) |
|  + DME Layer   |     |  + DME Layer   |
+-------+--------+     +--------+-------+
        |                       |
        |    Ricart-Agrawala    |
        |    DME Protocol       |
        |                       |
        v                       v
+---------------------------------------+
|           File Server (Node 3)        |
|         (Shared Chat File)            |
+---------------------------------------+
```

## Components

1. **file_server.py** - File server node maintaining shared chat file
2. **dme_middleware.py** - Ricart-Agrawala DME algorithm implementation
3. **chat_client.py** - Chat application using DME middleware

## How to Run

### Step 1: Start the File Server (Terminal 1)
```bash
python file_server.py
```

### Step 2: Start Client Node 1 (Terminal 2)
```bash
python chat_client.py node1 Lucy
```

### Step 3: Start Client Node 2 (Terminal 3)
```bash
python chat_client.py node2 Joel
```

## Commands

- `view` - View all messages (no lock needed, multiple viewers allowed)
- `post <message>` - Post a message (requires DME lock)
- `exit` - Exit the application

## DME Algorithm: Ricart-Agrawala

### How it works:
1. When a node wants to POST (enter critical section):
   - Sends REQUEST message to all other nodes
   - Waits for REPLY from all nodes

2. When a node receives REQUEST:
   - If not requesting/in CS: send REPLY immediately
   - If requesting: compare timestamps (lower = higher priority)
     - If own request has priority: defer REPLY
     - Otherwise: send REPLY immediately

3. When releasing CS:
   - Send all deferred REPLYs

### Logging
DME activity is logged to console with `[DME]` prefix to demonstrate the algorithm working.

## Sample Session

**Terminal 1 (Server):**
```
==================================================
CHAT ROOM FILE SERVER
==================================================
Host: localhost:9000
File: chat_messages.txt
Press Ctrl+C to stop
==================================================
```

**Terminal 2 (Lucy):**
```
Lucy> post "Welcome to the team project"
[Requesting write access...]
[Write access granted - posting message...]
[Message posted successfully]
[Write access released]

Lucy> view
----------------------------------------
20 Apr 09:01AM Lucy: Welcome to the team project
----------------------------------------
```

**Terminal 3 (Joel):**
```
Joel> view
----------------------------------------
20 Apr 09:01AM Lucy: Welcome to the team project
----------------------------------------

Joel> post "Thanks Lucy - hope to work together"
[Requesting write access...]
[Write access granted - posting message...]
[Message posted successfully]
[Write access released]
```

## Testing DME

To verify DME is working:
1. Open two client terminals
2. Try posting from both simultaneously
3. Observe the `[DME]` logs showing REQUEST/REPLY messages
4. Only one client will enter critical section at a time
