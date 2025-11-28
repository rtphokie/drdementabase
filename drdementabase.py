"""Utilities for parsing Dr. Demento show HTML and building a small database.

Contains helpers to normalize strings, extract show metadata from header lines,
and a simple main() that walks a directory of show HTML files producing a
DataFrame of tracks and first air dates.
"""

import pandas as pd
import re
from dateutil import parser


def remove_non_alphanumeric_regex(text):
    """Normalize a text string for keying by removing non-alphanumeric characters.

    - Converts to lowercase
    - Removes common suffixes/prefixes like ' cast' and leading 'the '
    - Removes parenthesized/bracketed substrings
    - Replaces some tokens ('&' -> 'and', 'soundtrack' variants)
    - Returns an empty string for None input

    Args:
        text (str|None): input text to normalize

    Returns:
        str: normalized, alphanumeric-only lowercase string
    """
    # The pattern '[^a-zA-Z0-9]' matches any character that is NOT
    # a lowercase letter (a-z), an uppercase letter (A-Z), or a digit (0-9).
    # The re.sub() function replaces all matches with an empty string.
    if text is None:
        result = ""
    else:
        text = text.lower()
        if text.endswith(" cast"):
            text = text[:-5]
        if text.startswith("the "):
            text = text[4:]
        text = text.replace(" the", "").replace(" & ", " and ").replace(" and ", " ")
        text = (
            text.replace(" cast ", "")
            .replace(" original soundtrack", " ")
            .replace(" soundtrack", " ")
        )
        cleaned = re.sub(r"\s*[\(\[][^\)\]]*?[\)\]]\s*", " ", text)
        result = re.sub(r"[^a-zA-Z0-9]", "", cleaned.lower())
    return result


def extract_show_info(show_string):
    """Parse a show header string to extract title, show number, and air date.

    The function recognizes several formats, for example:
      - "Title - Month Day, Year" -> title, None, datestr
      - "Title #123-45 - Month Day, Year" -> title, "123-45", datestr
      - "Title #XM-01 (XM channel 30)" -> title, "XM-01", None
      - "Title - posted Month Day, Year" -> title, None, datestr (with "posted" stripped)

    The returned show number is normalized (leading '#' removed). The returned
    parsed date is an ISO string "YYYY-MM-DD" when parsing succeeds, else None.

    Args:
        show_string (str): raw header line from an HTML show file

    Returns:
        tuple: (title (str), number (str|None), datestr (str|None), parsed_iso_date (str|None))
    """
    # Clean obvious artifacts
    show_string = show_string.replace("#XM ", "#XM").strip()
    show_string = show_string.replace("<H2>", "").replace("</H2>", "").strip()

    # Try patterns in order of priority:
    # 1) title [optional number] - datestr
    # 2) title [number] (maybe followed by parenthesized channel) (no date)
    # 3) title - datestr (no number)
    # 4) fallback: whole string as title
    #
    # We accept numbers that start with '#' followed by alphanumerics and dashes,
    # e.g. "#XM-01", "#123-45". We normalize by stripping the leading '#'.

    # Pattern 1: optional number before a hyphen-separated date
    match = re.match(
        r"(?P<title>.+?)(?:\s+(?P<number>#[A-Za-z0-9-]+)(?:\s*\([^)]*\))?)?\s*-\s*(?P<datestr>.+)",
        show_string,
    )
    # Pattern 2: title followed by a number and optional parenthetical (no hyphen/date)
    match_number_only = re.match(
        r"(?P<title>.+?)\s+(?P<number>#[A-Za-z0-9-]+)(?:\s*\([^)]*\))?\s*$", show_string
    )
    # Pattern 3: simple title - datestr (no number)
    match_simple = re.match(r"(?P<title>.+?)\s*-\s*(?P<datestr>.+)", show_string)

    number = None
    datestr = None
    parsed_date = None

    if match:
        title = match.group("title").strip()
        number = match.group("number").strip() if match.group("number") else None
        datestr = match.group("datestr").strip()
    elif match_number_only:
        title = match_number_only.group("title").strip()
        number = match_number_only.group("number").strip()
        datestr = None
    elif match_simple:
        title = match_simple.group("title").strip()
        number = None
        datestr = match_simple.group("datestr").strip()
    else:
        title = show_string
        number = None
        datestr = None

    # Normalize number: drop leading '#' if present
    if number:
        number = number.lstrip("#").strip()

    # Clean datestr of artifacts like "posted" and parentheses noise
    datestr = (
        datestr.replace(" posted", "").strip("posted ").strip() if datestr else None
    )

    # Existing date parsing heuristics largely preserved
    if datestr and ", " in datestr:
        try:
            datestr = datestr.replace("(?)", "").replace("197l", "1971")
            datestr = datestr.replace("Rocktober ", "October ").replace("?", "")
            atoms = datestr.split(" ")
            if " (" in datestr:
                datestr = " ".join(atoms[:3])
            if datestr.startswith("ring"):
                parsed_date = None
            else:
                try:
                    parsed_date = parser.parse(datestr.strip())
                except Exception as e:
                    print(e)
                    print(datestr)
                    raise
        except Exception as e:
            print(e)
            raise
            pass

    return (
        title,
        number,
        datestr,
        parsed_date.strftime("%Y-%m-%d") if parsed_date else None,
    )


def main():
    """Walk a directory of HTML files, extract tracks and show dates, build DataFrame.

    Returns:
        dict: mapping of normalized title -> normalized artist -> metadata dict
    """
    import os

    results = {}

    directory = "/Users/trice/PycharmProjects/sandbox/DrDementabase/drd"

    for filename in sorted(os.listdir(directory)):
        if filename.endswith(".html"):
            filepath = os.path.join(directory, filename)
            special_topic, showname, shownumber, showdatestr, showdate = (
                None,
                None,
                None,
                None,
                None,
            )
            with open(filepath, "r", encoding="utf-8") as file:
                for line in file.readlines():
                    if "<h2" in line.lower():
                        showname, shownumber, showdatestr, showdate = extract_show_info(
                            line
                        )

                    if "<!--" in line:
                        continue
                    if "Bobby Pickett interview" in line:
                        title = "Little Darlin'"
                        artist = "Bobby Pickett"
                        continue
                    if "<strong" in line.lower():
                        atoms = line.split("<STRONG>")
                        line = "<STRONG>" + atoms[1]
                    line = line.replace("<BR>", "").strip()
                    line = line.replace("<P>", "").strip()
                    line = line.replace("&amp;", "&").strip()
                    line = line.replace("&quot;", " ").strip()
                    line = line.replace('"', " ").strip()
                    # line = line.replace(" (excerpt)", "").strip()
                    line = line.replace("[online version only]", "").strip()
                    line = line.strip("/")

                    match_special = re.match(r"Special Topic:\s*(.+)", line.strip())
                    if match_special:
                        special_topic = match_special.group(1).strip()

                    match_track = re.match(
                        r"<strong>(.+?)</strong>"  # group(1): title
                        r"(?:\s*\(([^)]+)\))?"  # group(2): optional parenthesized note, e.g. "excerpt #1"
                        r"(?:\s*-\s*(.+))?",  # group(3): artist (optional)
                        line,
                        re.IGNORECASE,
                    )
                    if match_track:
                        title = match_track.group(1).strip()
                        note = (
                            match_track.group(2).strip()
                            if match_track.group(2)
                            else None
                        )
                        artist = (
                            match_track.group(3).strip()
                            if match_track.group(3)
                            else None
                        )
                        key_title = remove_non_alphanumeric_regex(
                            title
                        )  # normalize title
                        key_artist = remove_non_alphanumeric_regex(
                            artist
                        )  # normalize artist

                        if key_title not in results.keys():
                            results[key_title] = {}
                        if artist not in results[key_title].keys():
                            results[key_title][key_artist] = {
                                "title": title,
                                "artist": artist,
                                "shows": set(),
                                "first": None,
                            }
                        if showdate is not None:
                            # skip playlists without an air date
                            results[key_title][key_artist]["shows"].add(showdate)
                            results[key_title][key_artist]["first"] = min(
                                results[key_title][key_artist]["shows"]
                            )
                    elif "<strong" in line.lower():
                        print(f"Unmatched strong line: {line} in show {showname}")
                        pass
    return results


if __name__ == "__main__":
    results = main()
    rows = []
    for title in results.keys():
        for artist in results[title].keys():
            rows.append(results[title][artist])
    df = pd.DataFrame(rows, index=None)
    filename = "drdementabase.xlsx"
    df.to_excel(filename, index=False)
    print(f"Wrote {len(df)} tracks to {filename}")
