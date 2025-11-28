import unittest
import pandas as pd
from pprint import pprint
import re
from dateutil import parser

def remove_non_alphanumeric_regex(text):
    # The pattern '[^a-zA-Z0-9]' matches any character that is NOT
    # a lowercase letter (a-z), an uppercase letter (A-Z), or a digit (0-9).
    # The re.sub() function replaces all matches with an empty string.
    if text is None:
        result= ''
    else:
        text=text.lower()
        if text.endswith(' cast'):
            text=text[:-5]
        if text.startswith('the '):
            text=text[4:]
        text=text.replace(' the', '').replace(' & ', ' and ').replace(' and ', ' ')
        text=text.replace(' cast ', '').replace(' original soundtrack', ' ').replace(' soundtrack', ' ')
        cleaned = re.sub(r"\s*[\(\[][^\)\]]*?[\)\]]\s*", " ", text)
        result= re.sub(r'[^a-zA-Z0-9]', '', cleaned.lower())
    return result

def extract_show_info(show_string):
    show_string = show_string.replace("#XM ", "#XM").strip()
    show_string = show_string.replace("<H2>", "").replace("</H2>", "").strip()
    match = re.match(r"(.+?)(?: (#\d+-\d+))? - (.+)", show_string)
    match_xm = re.search(r"(.+?) (#[XM\-\d]+)", show_string)
    match_simple = re.match(r"(.+?) - (.+)", show_string)

    number = None
    datestr = None
    parsed_date = None

    if match:
        title = match.group(1).strip()
        number = match.group(2).strip() if match.group(2) else None
        datestr = match.group(3).strip()
    elif "XM" in show_string and match_xm:
        title = match_xm.group(1).strip()
        number = match_xm.group(2).strip()
        datestr = None
    elif match_simple:
        title = match_simple.group(1).strip()
        number = match_simple.group(2).strip()
        datestr = None
    else:
        title = show_string

    datestr = datestr.replace(" posted", "").strip('posted ').strip() if datestr else None
    if datestr and ", " in datestr:
        try:
            datestr = datestr.replace("(?)", "").replace('197l', '1971')  # assumed guessed dates are right
            datestr = datestr.replace("Rocktober ", "October ").replace('?', '')
            atoms=datestr.split(" ")
            if ' (' in datestr:
                datestr = ' '.join(atoms[:3])

            if datestr.startswith("ring"):
                parsed_date=None
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
    else:
        pass
    return title, number, datestr, parsed_date.strftime("%Y-%m-%d") if parsed_date else None


def main():
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
                    line=line.strip('/')

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
                        key_title=remove_non_alphanumeric_regex(title) # normalize title
                        key_artist=remove_non_alphanumeric_regex(artist) # normalize artist

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


class MyTestCase(unittest.TestCase):
    def test_something(self):
        results = main()
        rows=[]
        for title in results.keys():
            for artist in results[title].keys():
                rows.append(results[title][artist])
        df = pd.DataFrame(rows, index=None)
        print(df)
        df.to_excel("drdementabase.xlsx", index=False)

        # pprint(results)


if __name__ == "__main__":
    unittest.main()
