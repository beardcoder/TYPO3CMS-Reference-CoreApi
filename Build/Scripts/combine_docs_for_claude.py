#!/usr/bin/env python3
"""
Combines all RST documentation files into a single Markdown document.
Optimized for uploading to Claude as a knowledge document.

Usage:
    python3 Build/Scripts/combine_docs_for_claude.py

Output:
    claude-export/typo3-coreapi-complete.md
    claude-export/typo3-coreapi-complete.txt
"""
import re
import sys
from pathlib import Path


def rst_to_simple_markdown(content, base_path=None):
    """Convert RST to simplified Markdown for Claude."""
    lines = content.split('\n')
    output_lines = []
    in_code_block = False
    code_block_lang = ''
    skip_until_dedent = False
    base_indent = 0

    for line in lines:
        # Handle code blocks
        if re.match(r'\s*\.\. code-block::\s*(\w+)?', line):
            match = re.match(r'\s*\.\. code-block::\s*(\w+)?', line)
            code_block_lang = match.group(1) or ''
            in_code_block = True
            output_lines.append(f'```{code_block_lang}')
            continue

        if re.match(r'\s*\.\. literalinclude::', line):
            output_lines.append('```')
            output_lines.append(f'[Code from: {line.split("::")[-1].strip()}]')
            output_lines.append('```')
            continue

        # Skip directive options (lines starting with :)
        if re.match(r'\s+:\w+:', line) and not in_code_block:
            continue

        # Handle include directives by inlining the content
        include_match = re.match(r'\s*\.\. include::\s+(.+)', line)
        if include_match and base_path:
            include_file = include_match.group(1).strip()
            # Resolve path relative to Documentation/
            if include_file.startswith('/'):
                include_path = base_path.parent / include_file.lstrip('/')
            else:
                include_path = base_path / include_file
            
            try:
                if include_path.exists():
                    included_content = include_path.read_text(encoding='utf-8')
                    output_lines.append(f'\n<!-- Included from: {include_file} -->')
                    output_lines.append(rst_to_simple_markdown(included_content, include_path.parent))
                    output_lines.append('<!-- End include -->\n')
                else:
                    output_lines.append(f'<!-- Include not found: {include_file} -->')
            except Exception as e:
                output_lines.append(f'<!-- Error including {include_file}: {e} -->')
            continue

        # Handle directive blocks we want to skip
        if re.match(r'\s*\.\. (toctree|index|image|figure|only|ifconfig)::', line):
            skip_until_dedent = True
            base_indent = len(line) - len(line.lstrip())
            continue

        if skip_until_dedent:
            current_indent = len(line) - len(line.lstrip()) if line.strip() else base_indent + 1
            if line.strip() and current_indent <= base_indent:
                skip_until_dedent = False
            else:
                continue

        # Handle notes, warnings, etc. - convert to blockquotes
        if re.match(r'\s*\.\. (note|warning|important|tip|seealso|attention|caution|danger|error|hint)::', line):
            directive_type = re.match(r'\s*\.\. (\w+)::', line).group(1).upper()
            output_lines.append(f'\n> **{directive_type}:**')
            continue

        # Convert RST headers to Markdown
        if re.match(r'^[=]+$', line.strip()) and output_lines:
            if output_lines[-1].strip():
                output_lines[-1] = f'# {output_lines[-1].strip()}'
            continue
        if re.match(r'^[-]+$', line.strip()) and output_lines:
            if output_lines[-1].strip():
                output_lines[-1] = f'## {output_lines[-1].strip()}'
            continue
        if re.match(r'^[~]+$', line.strip()) and output_lines:
            if output_lines[-1].strip():
                output_lines[-1] = f'### {output_lines[-1].strip()}'
            continue
        if re.match(r'^[\^]+$', line.strip()) and output_lines:
            if output_lines[-1].strip():
                output_lines[-1] = f'#### {output_lines[-1].strip()}'
            continue

        # Handle inline code and references
        line = re.sub(r':ref:`([^`]+)`', r'[\1]', line)
        line = re.sub(r':php:`([^`]+)`', r'`\1`', line)
        line = re.sub(r':typoscript:`([^`]+)`', r'`\1`', line)
        line = re.sub(r':yaml:`([^`]+)`', r'`\1`', line)
        line = re.sub(r':sql:`([^`]+)`', r'`\1`', line)
        line = re.sub(r':file:`([^`]+)`', r'`\1`', line)
        line = re.sub(r':command:`([^`]+)`', r'`\1`', line)
        line = re.sub(r':guilabel:`([^`]+)`', r'**\1**', line)
        line = re.sub(r':kbd:`([^`]+)`', r'`\1`', line)
        line = re.sub(r':abbr:`([^`]+)`', r'\1', line)
        line = re.sub(r'``([^`]+)``', r'`\1`', line)

        # End code block on dedent
        if in_code_block and line.strip() and not line.startswith('   ') and not line.startswith('\t'):
            output_lines.append('```')
            in_code_block = False

        output_lines.append(line)

    if in_code_block:
        output_lines.append('```')

    return '\n'.join(output_lines)


def process_documentation():
    """Process all documentation files."""
    # Determine project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    docs_path = project_root / 'Documentation'
    export_path = project_root / 'claude-export'

    if not docs_path.exists():
        print(f"Error: Documentation directory not found at {docs_path}")
        sys.exit(1)

    export_path.mkdir(exist_ok=True)

    output = []

    # Add header
    output.append('# TYPO3 Core API Reference')
    output.append('')
    output.append('This document is a comprehensive reference for TYPO3 CMS Core API.')
    output.append('Generated from the official TYPO3 documentation.')
    output.append('Source: https://github.com/TYPO3-Documentation/TYPO3CMS-Reference-CoreApi')
    output.append('')
    output.append('---')
    output.append('')

    total_files = 0

    # First, process top-level RST files
    top_level_files = ['Index.rst', 'About.rst', 'Sitemap.rst']
    for filename in top_level_files:
        file_path = docs_path / filename
        if file_path.exists():
            try:
                content = file_path.read_text(encoding='utf-8')
                output.append(f'\n\n# Document: {filename}\n')
                output.append('=' * 80)
                output.append('')
                output.append(rst_to_simple_markdown(content, file_path.parent))
                total_files += 1
            except Exception as e:
                print(f'Warning: Error processing {file_path}: {e}')

    # Define the order of main sections - include all directories
    section_order = [
        'Introduction',
        'ApiOverview',
        'ExtensionArchitecture',
        'Configuration',
        'CodingGuidelines',
        'PhpArchitecture',
        'Security',
        'Testing',
        'Administration',
        'CodeSnippets',  # Include code snippets as they contain examples
    ]

    total_files = 0

    # Process sections in order
    for section in section_order:
        section_path = docs_path / section
        if section_path.exists():
            section_title = section.replace("Api", "API ")
            output.append(f'\n\n# {section_title}\n')
            output.append('=' * 80)
            output.append('')

            # Find all RST files in this section
            rst_files = sorted(section_path.rglob('*.rst'))
            for rst_file in rst_files:
                if rst_file.name.startswith('_'):
                    continue
                try:
                    content = rst_file.read_text(encoding='utf-8')
                    relative_path = rst_file.relative_to(docs_path)
                    output.append(f'\n\n## File: {relative_path}\n')
                    output.append('-' * 60)
                    output.append('')
                    output.append(rst_to_simple_markdown(content, rst_file.parent))
                    total_files += 1
                except Exception as e:
                    print(f'Warning: Error processing {rst_file}: {e}')

    # Combine output
    combined = '\n'.join(output)

    # Write Markdown version
    md_path = export_path / 'typo3-coreapi-complete.md'
    md_path.write_text(combined, encoding='utf-8')

    # Write plain text version (for maximum compatibility)
    txt_path = export_path / 'typo3-coreapi-complete.txt'
    txt_path.write_text(combined, encoding='utf-8')

    # Calculate sizes
    size_kb = len(combined.encode('utf-8')) / 1024
    size_mb = size_kb / 1024

    print(f'Created combined documentation:')
    print(f'  - {md_path.name}: {size_kb:.0f} KB ({size_mb:.2f} MB)')
    print(f'  - {txt_path.name}: {size_kb:.0f} KB ({size_mb:.2f} MB)')
    print(f'  - Processed {total_files} RST files')
    print(f'  - Total characters: {len(combined):,}')

    # Split if file is too large for Claude
    if size_kb > 700:
        print(f'\nFile is {size_kb:.0f} KB - splitting for Claude compatibility...')
        split_document(combined, export_path, 'typo3-coreapi', max_size_kb=600)


def split_document(content, export_path, base_name, max_size_kb=600):
    """Split large document into Claude-friendly chunks by section."""
    lines = content.split('\n')
    parts = []
    current_part = []
    current_size = 0
    max_size_bytes = max_size_kb * 1024

    # Track section boundaries for smart splitting
    section_indices = []
    for i, line in enumerate(lines):
        if line.startswith('# ') and not line.startswith('# TYPO3'):
            section_indices.append(i)

    if not section_indices:
        section_indices = [0]

    # Split by major sections
    for i, section_start in enumerate(section_indices):
        section_end = section_indices[i + 1] if i + 1 < len(section_indices) else len(lines)
        section_lines = lines[section_start:section_end]
        section_text = '\n'.join(section_lines)
        section_size = len(section_text.encode('utf-8'))

        # If a single section exceeds max size, split it further
        if section_size > max_size_bytes:
            # Try splitting on ## boundaries within the section
            subsection_parts = split_oversized_section(section_lines, max_size_bytes)
            for subsection_part in subsection_parts:
                if current_size + len(subsection_part.encode('utf-8')) > max_size_bytes and current_part:
                    parts.append('\n'.join(current_part))
                    current_part = []
                    current_size = 0
                
                current_part.extend(subsection_part.split('\n'))
                current_size += len(subsection_part.encode('utf-8'))
        elif current_size + section_size > max_size_bytes and current_part:
            parts.append('\n'.join(current_part))
            current_part = []
            current_size = 0
            current_part.extend(section_lines)
            current_size += section_size
        else:
            current_part.extend(section_lines)
            current_size += section_size

    if current_part:
        parts.append('\n'.join(current_part))

    # Write parts
    print(f'Created {len(parts)} split files:')
    for i, part in enumerate(parts, 1):
        # Add header to each part
        part_with_header = f'# TYPO3 Core API Reference - Part {i} of {len(parts)}\n\n{part}'

        part_md = export_path / f'{base_name}-part{i}.md'
        part_txt = export_path / f'{base_name}-part{i}.txt'

        part_md.write_text(part_with_header, encoding='utf-8')
        part_txt.write_text(part_with_header, encoding='utf-8')

        size_kb = len(part_with_header.encode('utf-8')) / 1024
        print(f'  - {part_md.name}: {size_kb:.0f} KB')


def split_oversized_section(section_lines, max_size_bytes):
    """Split an oversized section into smaller parts at ## boundaries."""
    parts = []
    current_part = []
    current_size = 0

    for line in section_lines:
        line_size = len((line + '\n').encode('utf-8'))
        
        # If we hit a ## boundary and current part is getting large, split
        if line.startswith('## ') and current_size + line_size > max_size_bytes * 0.8:
            if current_part:
                parts.append('\n'.join(current_part))
                current_part = []
                current_size = 0
        
        current_part.append(line)
        current_size += line_size
        
        # Force split if we've exceeded the max size
        if current_size > max_size_bytes:
            parts.append('\n'.join(current_part))
            current_part = []
            current_size = 0

    if current_part:
        parts.append('\n'.join(current_part))

    return parts


if __name__ == '__main__':
    process_documentation()
