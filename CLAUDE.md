# Data Import Guidelines

## Core Principles
- Data accuracy and integrity are paramount
- Map XML to SQL directly unless instructed otherwise
- Document everything thoroughly

## Data Handling Rules
1. **Validation**: Always validate and sanitize inputs
2. **Error Handling**: Implement comprehensive error handling and logging
3. **Backups**: Regular data backups required
4. **Documentation**: Document schema and transformations

## Import Process
- Run direct Python code (no test scripts)
- Check for existing models before creating new ones (watch for naming variations)
- Create related models and relations as needed
- Import, process, and store every property
- Design unified data model across all legislative periods (no versioned tables)
- When marking fields as "mapped", ensure you rely on the full hierarchy of the XML document, to prevent mixing fields from different contexts with the same name.
- data integrity guideline: use only data that matches the source exactly, never generate artificial data or provide defaults.
- 
## Field Management
- Don't derive fields from other fields without explicit data
- New fields allowed if well-justified and documented
- Document understanding of each field
- Update documentation when gaining new knowledge

## Workflow
- No commits without approval
- Request code review when ready
- Iterate based on feedback until approved

## Schema Error Resolution
1. Check existing models (including poorly named ones)
2. Create/update related models if needed
3. Add necessary relations and fields
4. Ensure complete data import