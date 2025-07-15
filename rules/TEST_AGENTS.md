# Test des Agents RooCode dans Cursor

## 🧪 Tests rapides à effectuer

### 1. Redémarrez Cursor
- Fermez complètement Cursor
- Rouvrez Cursor dans ce projet
- OU utilisez `Cmd+Shift+P` → "Developer: Reload Window"

### 2. Testez ces agents dans le chat Cursor :

#### Test 1 - Orchestrateur principal
```
@uber_orchestrator_agent Bonjour ! Peux-tu me confirmer que tu es actif ?
```

#### Test 2 - Agent de développement
```
@coding_agent Écris une fonction JavaScript simple qui dit "Hello World"
```

#### Test 3 - Agent de documentation
```
@scribe_agent Documente brièvement ce projet
```

#### Test 4 - Agent de design
```
@ui_designer_agent Suggère une palette de couleurs pour une application moderne
```

### 3. Vérifications alternatives

Si les agents ne répondent pas avec `@`, essayez :

#### Dans les paramètres Cursor :
1. Ouvrez les paramètres (`Cmd+,` ou `Ctrl+,`)
2. Cherchez "Rules" ou "Custom Instructions"
3. Vérifiez que le fichier `.cursorrules` est détecté

#### Test manuel :
Copiez cette instruction dans le chat :
```
Tu es l'uber-orchestrator-agent. Tu es le chef d'orchestre suprême des projets complexes. 
Réponds-moi en tant que cet agent spécialisé.
```

### 4. Liste des 67 agents disponibles

Voici quelques agents clés à tester :

**🎩 Orchestration :**
- @uber_orchestrator_agent
- @task_planning_agent
- @project_initiator_agent

**💻 Développement :**
- @coding_agent
- @code_reviewer_agent
- @system_architect_agent

**🎨 Design :**
- @ui_designer_agent
- @ux_researcher_agent
- @design_system_agent

**🧪 Tests :**
- @test_orchestrator_agent
- @functional_tester_agent
- @security_auditor_agent

**📝 Documentation :**
- @scribe_agent
- @documentation_agent
- @elicitation_agent

**📊 Marketing :**
- @marketing_strategy_orchestrator
- @seo_sem_agent
- @content_strategy_agent

### 5. Dépannage

Si ça ne fonctionne toujours pas :

1. **Vérifiez le fichier .cursorrules :**
   ```bash
   head -10 .cursorrules
   ```

2. **Vérifiez la version de Cursor :**
   - Assurez-vous d'avoir une version récente de Cursor

3. **Essayez la méthode manuelle :**
   - Copiez le contenu d'un agent depuis `cursor_config/cursor_instructions/`
   - Collez-le dans les paramètres Custom Instructions de Cursor

4. **Redémarrez votre ordinateur :**
   - Parfois nécessaire pour que Cursor détecte les nouveaux fichiers

## ✅ Confirmation de fonctionnement

Quand ça marche, vous devriez voir :
- Les agents répondent avec leur personnalité spécifique
- Ils mentionnent leur rôle et spécialité
- Ils utilisent les emojis et le style défini dans leur configuration

Bonne chance ! 🚀 