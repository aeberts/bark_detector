# ⚠️ LEGACY TEMPLATES - DEPRECATED ⚠️

**STATUS**: These templates have been SUPERSEDED by BMad Method templates
**REPLACEMENT**: Use professional BMad templates in `.bmad-core/templates/`
**DO NOT USE**: These pre-BMad templates conflict with current BMad standards
**DATE ARCHIVED**: 2025-09-24

---

## BMad Method Migration Guide

This templates/ directory contained pre-BMad generic templates that have been replaced by:

### BMad Professional Templates (`.bmad-core/templates/`)
- `prd-tmpl.yaml` - Professional PRD template with epic structure
- `story-tmpl.yaml` - BMad story template with proper workflow states
- `architecture-tmpl.yaml` - Architecture documentation template
- `brownfield-architecture-tmpl.yaml` - Brownfield system documentation
- Plus many more specialized templates

### BMad Agent Integration
- **Template Creation**: Use BMad Master `*create-doc {template}` command
- **Template Selection**: Agents automatically use appropriate BMad templates
- **Professional Standards**: BMad templates follow industry best practices

### Legacy Template Migration
- **prd_template.md** → Use `.bmad-core/templates/prd-tmpl.yaml`
- **user_story_template.md** → Use `.bmad-core/templates/story-tmpl.yaml`
- **session_restart.md** → Superseded by BMad agent workflows

---

## Archived Templates

The files in this directory are kept for historical reference only. For current work:

1. **Use BMad Master**: `*create-doc {template}` to see available templates
2. **Professional Quality**: BMad templates are industry-standard YAML-based
3. **Agent Integration**: Templates work seamlessly with BMad agents
4. **Workflow Integration**: Templates support proper Epic → Story → Implementation flow

**DO NOT use these legacy Markdown templates - they lack BMad workflow integration.**