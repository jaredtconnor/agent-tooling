# File Extraction Rules for Sub-Page Content

When writing additional skill files from Notion sub-pages, use these rules to determine how to extract content.

## Determining Extraction Method

The sub-page **title** is the **filename**. Use the file extension to decide whether to extract from a code block or write as-is:

| Extension | Code block expected? | Extraction |
|-----------|---------------------|------------|
| `.md` | No | Write content as-is |
| `.html` | Yes | Extract from code block |
| `.css`, `.scss` | Yes | Extract from code block |
| `.js`, `.ts` | Yes | Extract from code block |
| `.py` | Yes | Extract from code block |
| `.sh` | Yes | Extract from code block |
| `.json` | Yes | Extract from code block |
| `.yaml`, `.yml` | Yes | Extract from code block |
| `.sql` | Yes | Extract from code block |
| Other | Maybe | Check for code block — extract if present, otherwise write as-is |

## Code Block Extraction

When extracting from a code block:

1. Find the opening triple backticks (with optional language tag)
2. Extract only the content **between** the opening and closing backtick fences
3. Strip the backtick wrappers and language tag
4. Write the extracted inner content to the file

Example — a sub-page titled `config.json` with body:

````
Here is the configuration:

```json
{
  "key": "value"
}
```
````

Write to `config.json`:

```json
{
  "key": "value"
}
```

## Markdown Files (.md)

For `.md` sub-pages, write the full page body as-is — do not look for or strip code block wrappers. The content is already valid markdown.
