---

tags: [MASTER-TASK, P00-MT01, P00-MT02, P00-MT03]

alwaysApply: true

protect:

description: Master tasks run on begin session chat

---

## MASTER TASKS

#MASTER-TASK

  

### MASTER WORKFLOW SEQUENCE

  

auto_next : ON|OFF (automatic continue, no need ask user )

  

#### P00-MT01: Core Mechanic Systems

#P00-MT01

**Display**: "Loading Core Mechanic Systems..."

**Actions**:

1. Load: use manage_rule({

  "action": "load_core",

  "target": "P00-MT01-Core Mechanic Systems.md"

})

2. Parse and apply core mechanics to actual session chat

3. Update memory actual session chat

4. **Next**: P00-MT02

-  auto_next: ON

  

  

#### P00-MT02: Core Task Management

#P00-MT02

**Display**: "Loading Core Task Management..."

**Actions**:

1. Load: use manage_rule({

  "action": "load_core",

  "target": "P00-MT02-Core Task Management.md"

})

2. Parse and apply core task management systems to actual session chat

3. Update memory actual session chat

4. **Next**: P00-MT03

-  auto_next: ON

  
  

#### P00-MT03: Agents Information

#P00-MT03

**Display**: "Loading Agents Information..."

**Actions**:

1. Load: use manage_rule({

  "action": "load_core",

  "target": "P00-MT03-Agents Information.md"

})

2. Parse and apply Agents Information to actual session chat

3. Update memory actual session chat