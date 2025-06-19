from __future__ import annotations

import re
from typing import final


@final
class MarkdownChunker:
    def __init__(self, max_length: int = 2000) -> None:
        self.max_length = max_length
        self.code_block_pattern = re.compile(r"^```(\w+)?$")

    def split(self, markdown_text: str) -> list[str]:
        """Split markdown text into chunks that never exceed max_length."""
        if len(markdown_text) <= self.max_length:
            return [markdown_text]

        lines = markdown_text.splitlines(keepends=True)
        chunks = []
        current_chunk = []
        current_length = 0
        in_code_block = False
        code_lang = ""

        for line in lines:
            # Handle extremely long single lines
            current_line = line
            if len(current_line) > self.max_length:
                current_line = self._truncate_line(current_line)

            is_code_fence = self.code_block_pattern.match(current_line.strip())

            # Update code block state
            if is_code_fence:
                if not in_code_block:
                    in_code_block = True
                    code_lang = is_code_fence.group(1) or ""
                else:
                    in_code_block = False
                    code_lang = ""

            # Check if we need to start a new chunk
            space_needed = self._calculate_space_needed(
                current_line,
                in_code_block=in_code_block,
            )
            if current_length + space_needed > self.max_length and current_chunk:
                # Finalize current chunk
                chunk_text = self._finalize_chunk(
                    current_chunk,
                    in_code_block=in_code_block,
                )
                chunks.append(chunk_text)

                # Start new chunk
                current_chunk = []
                current_length = 0

                # Reopen code block in new chunk if needed
                if in_code_block and not is_code_fence:
                    opening_fence = f"```{code_lang}\n"
                    current_chunk.append(opening_fence)
                    current_length = len(opening_fence)

            # Add line to current chunk
            current_chunk.append(current_line)
            current_length += len(current_line)

        # Handle final chunk
        if current_chunk:
            chunk_text = self._finalize_chunk(
                current_chunk,
                in_code_block=in_code_block,
            )
            chunks.append(chunk_text)

        return self._ensure_valid_chunks(chunks, markdown_text)

    def _truncate_line(self, line: str) -> str:
        """Truncate a line that exceeds max_length."""
        if len(line) <= self.max_length:
            return line

        truncated = line[: self.max_length - 1]
        if not line.endswith("\n"):
            truncated += "\n"
        return truncated

    def _calculate_space_needed(self, line: str, *, in_code_block: bool) -> int:
        """Calculate space needed for a line, including potential code block closing."""
        line_length = len(line)
        closing_fence_length = 4 if in_code_block else 0  # "```\n"
        return line_length + closing_fence_length

    def _finalize_chunk(self, chunk_lines: list[str], *, in_code_block: bool) -> str:
        """Finalize a chunk, ensuring it doesn't exceed max_length."""
        if not chunk_lines:
            return ""

        # Add closing fence if needed
        if in_code_block:
            closing_fence = "```\n"
            chunk_lines_copy = chunk_lines.copy()
            chunk_lines_copy.append(closing_fence)

            # Check if adding closing fence exceeds limit
            test_chunk = "".join(chunk_lines_copy)
            if len(test_chunk) <= self.max_length:
                chunk_lines = chunk_lines_copy
            else:
                # Remove lines until we can fit the closing fence
                while (
                    chunk_lines
                    and len("".join(chunk_lines) + closing_fence) > self.max_length
                ):
                    chunk_lines.pop()
                if chunk_lines:
                    chunk_lines.append(closing_fence)

        chunk_text = "".join(chunk_lines)

        # Final safety check
        if len(chunk_text) > self.max_length:
            chunk_text = chunk_text[: self.max_length]

        return chunk_text

    def _ensure_valid_chunks(self, chunks: list[str], original_text: str) -> list[str]:
        """Ensure all chunks are valid and non-empty."""
        valid_chunks = []

        for chunk in chunks:
            if chunk.strip():  # Only add non-empty chunks
                if len(chunk) <= self.max_length:
                    valid_chunks.append(chunk)
                else:
                    # Emergency fallback
                    valid_chunks.append(chunk[: self.max_length])

        # If no valid chunks, return truncated original
        if not valid_chunks:
            valid_chunks = [original_text[: self.max_length]]

        return valid_chunks


markdown_chunker = MarkdownChunker()
