"""Collection of functions to check that markdown links are valid."""

import re
from pathlib import Path
from terminal_utils import iprint, iprint_pass, iprint_fail

LINKS_REGEX = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
HEADING_REGEX = re.compile(r"^#+ (.*)")


class MarkdownLink:
    """Contains information about a markdown link."""

    def __init__(self, filepath: Path, line: int, link_text: str, link_url: str):
        """Create a MarkdownLink object."""
        self.filepath = filepath
        self.line = line
        self.link_text = link_text
        self.link_url = link_url
        self.url = ""
        self.anchor = ""
        self.title = ""

    def parse_link_url(self) -> None:
        """Parse the link into parts for further processing."""
        match self.link_url.count(" "):
            case 0:
                url_anchor = self.link_url  # potentially has URL and anchor but no title
            case _:
                # split at first space only because title may contain spaces as
                url_anchor, self.title = self.link_url.split(" ", 1)
        match url_anchor.count("#"):
            case 0:
                self.url = url_anchor  # only URL, no anchor
            case 1:
                self.url, self.anchor = url_anchor.split("#")
            case _:
                raise ValueError(f"invalid link '{self.link_url}' has too many hashtags in it.")

    @property
    def location(self) -> str:
        """Return a string that contains the filename and the line number for error reporting."""
        return f"{self.filepath}:{self.line}"

    def __str__(self) -> str:
        """Print for debugging purposes."""
        return f"{self.link_url=} {self.url=} {self.anchor=} {self.title=}"


def check_links_in_markdown(markdown_filename: Path) -> int:
    """Check links in a markdown file."""
    links = get_links(markdown_filename)
    error_message: list[str] = []
    for link in links:
        error_message += check_link(link)
    if error_message:
        iprint_fail(f"Link issues found in {markdown_filename.name}", 1)
        for message in error_message:
            iprint(message, 2)
        return 1
    iprint_pass(f"Links checked OK: {markdown_filename.name}", 1)
    return 0  # Success


def get_links(markdown_filename: Path) -> list[MarkdownLink]:
    """Return a list of links found in a markdown file."""
    markdown_links: list[MarkdownLink] = []
    with open(markdown_filename, encoding="utf8") as file:
        markdown = file.readlines()
        for line_number, line_text in enumerate(markdown):
            links = list(LINKS_REGEX.findall(line_text))
            for link in links:
                markdown_link = MarkdownLink(
                    markdown_filename,
                    line_number + 1,
                    link[0],
                    link[1],
                )
                markdown_links.append(markdown_link)
        return markdown_links


def check_link(link: MarkdownLink) -> list[str]:
    """Check a link for any issues."""
    error_message: list[str] = []

    try:
        link.parse_link_url()
    except ValueError as error:
        return [f"{link.location} - {error}"]

    # Check name of link
    # error_message += check_link_name(link.text)

    # Check whether it is an external link
    if link.url.startswith("https://"):
        error_message += check_external_link(link.url)
    else:
        error_message += check_internal_link(link)
    return error_message


def check_link_name(link_text: str) -> list[str]:
    """Check that the name of link text makes sense."""
    # This may be useful when transitioning from src to example.
    if "src" in link_text:
        return ["Link of text contains 'src'."]
    return []


def check_internal_link(link: MarkdownLink) -> list[str]:
    """Check validity of internal link."""
    if link.url:
        # Link has both a part (relative path) before hashtag, and a part (anchor) after hashtag
        target_filepath = link.filepath.parent / link.url
    else:
        # Link starts with hashtag and only has the anchor part
        target_filepath = link.filepath

    if not target_filepath.exists():
        return [f"{link.location} - '{str(target_filepath)}' does not exist"]
    if link.anchor:
        if not anchor_exists(target_filepath, link.anchor):
            return [f"{link.location} - invalid anchor '{link.anchor}' in link '{link.url}'"]
    return []


def anchor_exists(filepath: Path, anchor: str) -> bool:
    """Check whether an anchor link exists."""
    heading_anchors: list[str] = []
    with open(filepath, encoding="utf8") as file:
        markdown = file.readlines()
        for line in markdown:
            result = HEADING_REGEX.findall(line)
            if result:
                heading_anchors.append(normalize(result[0]))
    return anchor in heading_anchors


def check_external_link(url: str) -> list[str]:
    """Check validity of external link."""
    assert url
    return []


def normalize(header: str) -> str:
    """Normalize a header string for comparing against anchor text."""
    new_header = re.sub(r"[-_ ]+", "-", header.strip().replace("`", "")).lower()
    return new_header
