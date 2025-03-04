from datetime import date
import json

# import os
import re
from utf8totex import utf8totex

students = {
    "raileanu":slice(2015,2017),
    "el-badry":slice(2018,2019),
    "vijayan":slice(2018,2020),
    "woorak":slice(2020,2024),
    "kado-fong":slice(2018,2022),
    "mao":slice(2018,2022),
    "moon":slice(2020,2023),
    "lancaster":slice(2020,2023),
    "gong":slice(2015,2018),
    "guo":slice(2020,2025),
    "linzer":slice(2020,2025)
}

_JOURNAL_MAP = {
    "ArXiv e-prints": "ArXiv",
    "The Astronomical Journal": "\\aj",
    "The Astrophysical Journal": "\\apj",
    "The Astrophysical Journal Supplement Series": "\\apjs",
    "Astronomy and Astrophysics": "\\aanda",
    "Galaxies": "MDPI: galaxies",
    "The Journal of Open Source Software": "JOSS",
    "Monthly Notices of the Royal Astronomical Society": "\\mnras",
    "Nature": "\\nature",
    "Nature Astronomy": "\\natureast",
    "Publications of the Astronomical Society of the Pacific": "\\pasp",
    "Publications of the Astronomical Society of Japan": "\\pasj",
    "Publications of the Astronomical Society of Australia": "\\pasa",
}

JOURNAL_SKIP = [
    "VizieR Online Data Catalog",
    "^American Astronomical Society.*",
    "^AAS.*",
    "Astrophysics Source Code Library",
    "Zenodo Software Release",
    "Ph.D. Thesis",
    "Spitzer Proposal",
    "Rediscovering Our Galaxy",
    "The Astronomer's Telegram",
]
JOURNAL_SKIP = [x.lower() for x in JOURNAL_SKIP]

# Lower case journals:
JOURNAL_MAP = {}
for k, v in _JOURNAL_MAP.items():
    JOURNAL_MAP[k.lower()] = v

def in_slice(number, slc):
    return (int(number) >= slc.start) & (int(number) <= slc.stop)

def format_name(name):
    try:
        last, others = name.split(", ")
        others = ["{0}.".format(o[0]) for o in others.split()]
        name = "{last}, {first}".format(first=" ".join(others), last=last)

    except ValueError:
        print("couldn't format name '{0}'".format(name))

    return name


def parse_authors(paper_dict, max_authors=4):
    year = paper_dict["year"]
    raw_authors = [utf8totex(x) for x in paper_dict["authors"]]

    show_authors = raw_authors[:max_authors]

    if any(["chang-goo" in x.lower() for x in show_authors]):
        # Bold my name because it makes the cut to be shown
        names = []
        for i, name in enumerate(show_authors):
            if "chang-goo" in name.lower():
                name = "\\textbf{Kim, Chang-Goo}"
            else:
                if i == 0:
                    for stuname in students:
                        if (stuname in name.lower()) & in_slice(year, students[stuname]):
                            # print(name, year, students[stuname])
                            name = "\\student{" + name + "}"
            names.append(name)

        author_tex = "; ".join(names)

        if len(show_authors) < len(raw_authors):  # use et al.
            author_tex = author_tex + "~\\textit{et al.}"

    else:
        # Add "incl. CGK" after et al., because I'm buried in the author list
        # n_authors = len(raw_authors)
        # for i,x in enumerate(raw_authors):
        #     if ('chang-goo' in x.lower()) or ("Kim, C. -G." in x):
        #         i_author = i+1
        author_tex = "{0}".format(format_name(show_authors[0]))
        author_tex += "~\\textit{et al.}~(incl. \\textbf{CGK})"
        # author_tex += "~\\textit{et al.}~(incl. \\textbf{CGK}"
        # author_tex += "; {}/{})".format(i_author,n_authors)
        # print(i_author,n_authors)

    return author_tex


def filter_papers(pubs):
    filtered = []

    for p in pubs:
        if p["pub"] is None:
            continue

        # Skip if the publication is in the skip list:
        if any(
            [re.match(re.compile(pattr), p["pub"].lower()) for pattr in JOURNAL_SKIP]
        ):
            continue

        if p["pub"].lower() != "arxiv e-prints":
            pub = JOURNAL_MAP.get(p["pub"].strip("0123456789# ").lower(), None)

            if pub is None:
                # print("Journal '{0}' not recognized for paper '{1}' - "
                #      " skipping...".format(p['pub'], p['title']))
                continue

        # HACK: hard-coded skip
        if "astropy problem" in p["title"].lower():
            continue

        filtered.append(p)

    return filtered


def get_paper_items(papers, periods=None):
    refereeds = []
    preprints = []

    first_refs = []
    sec_refs = []
    other_refs = []
    for paper in papers:
        authors = parse_authors(paper)
        entry = authors

        # Skip if the publication is in the skip list:
        if any(
            [
                re.match(re.compile(pattr), paper["pub"].lower())
                for pattr in JOURNAL_SKIP
            ]
        ):
            continue

        # if paper["doi"] is not None:
        #     title = "\\doiform{{{0}}}{{{1}}}".format(paper["doi"],
        #                                          utf8totex(paper["title"]))
        # else:
        title = "\\textit{{{0}}}".format(utf8totex(paper["title"]))
        if "<SUB>" in title:
            title = title.replace("<SUB>", "${}_{").replace("</SUB>", "}$")
            print(title)
        entry += ", " + title

        if paper["pub"] not in [None, "ArXiv e-prints", "arXiv e-prints"]:  # HACK
            pub = JOURNAL_MAP.get(paper["pub"].strip("0123456789# ").lower(), None)

            if pub is None:
                print(
                    "Journal '{0}' not recognized for paper '{1}' - "
                    " skipping...".format(paper["pub"], paper["title"])
                )
                continue
            if paper["doi"] is not None:
                pub = "\\doiform{{{0}}}{{{1}}}".format(paper["doi"], pub)
            entry += ", " + pub
            is_preprint = False
        else:
            is_preprint = True

        if paper["volume"] is not None:
            entry += ", \\textbf{{{0}}}".format(paper["volume"])

        if paper["page"] is not None:
            entry += ", {0}".format(paper["page"])

        if paper["pubdate"] is not None:
            entry += ", {0}".format(paper["pubdate"].split("-")[0])

        if paper["arxiv"] is not None:
            entry += " (\\arxiv{{{0}}})".format(paper["arxiv"])

        if paper["citations"] > 1:
            entry += " [\\href{{{0}}}{{{1} citations}}]".format(
                paper["url"], paper["citations"]
            )

        if is_preprint:
            # if "armillotta" in paper["authors"][0].lower():
            #     entry += ", ApJ in press"
            #     is_preprint = False

            if "kraft" in paper["authors"][0].lower():
                continue
            else:
                entry += ", ApJ submitted"

        if periods is not None:
            d1 = date.fromisoformat(periods[0])
            d2 = date.fromisoformat(periods[1])
            pubdate = date.fromisoformat(paper["pubdate"].replace("00", "01"))
            if (pubdate < d1) | (pubdate > d2):
                continue

        if is_preprint:
            preprints.append(entry)
        else:
            refereeds.append(entry)
            myname = "Chang-Goo"
            if myname in paper["authors"][0]:
                first_refs.append(entry)
            elif (
                ((len(paper["authors"]) > 1) and (myname in paper["authors"][1]))
                or ("student" in authors)
                or (
                    ("munan" in paper["authors"][0].lower())
                    and (myname in paper["authors"][2])
                )
                or ("jeong-gyu" in paper["authors"][0].lower())
                or ("sultan" in paper["authors"][0].lower())
                or ("sarah" in paper["authors"][0].lower())
            ):
                print(paper["authors"][0])
                sec_refs.append(entry)
            else:
                other_refs.append(entry)

    # Now go through and add the \item and numbers:
    for corpus in [preprints]:
        for i, item in enumerate(corpus):
            corpus[i] = "\\item " + item
    for corpus in [refereeds]:
        for i, item in enumerate(corpus):
            num = len(corpus) - i
            corpus[i] = "\\item[{" + str(num) + ".}]" + item

    nums = range(len(refereeds) + 1)[::-1]
    j = 0
    for corpus in [first_refs, sec_refs, other_refs]:
        for i, item in enumerate(corpus):
            # num = j+1 #
            num = nums[j]
            corpus[i] = "\\item[{" + str(num) + ".}]" + item
            j += 1

    return refereeds, preprints, first_refs, sec_refs, other_refs


if __name__ == "__main__":
    from os import path

    dirpath = path.join(path.dirname(__file__), "../data")
    pubs_file = path.join(dirpath, "pubs.json")
    if not path.exists(pubs_file):
        raise FileNotFoundError(
            "File 'pubs.json' not found - run get_pubs.py "
            "before running this script."
        )

    with open(pubs_file, "r") as f:
        pubs = json.loads(f.read())

    papers = filter_papers(pubs)
    refs, unrefs, first_refs, sec_refs, other_refs = get_paper_items(papers)

    # Compute citation stats
    nref = len(refs)
    cites = sorted((p["citations"] for p in papers), reverse=True)
    ncitations = sum(cites)

    # Compute for specific conditions
    myname = "Chang-Goo"
    nfirst = 0
    nsec = 0
    cites_first = []
    cites_sec = []
    for p in papers:
        if myname in p["authors"][0]:
            nfirst += 1
            cites_first.append(p["citations"])
        elif len(p["authors"]) > 1:
            authors = parse_authors(p)
            if (myname in p["authors"][1]) or ("student" in authors):
                nsec += 1
                cites_sec.append(p["citations"])
    cites_first = sorted(cites_first, reverse=True)
    ncitations_first = sum(cites_first)
    cites_sec = sorted(cites_sec, reverse=True)
    ncitations_sec = sum(cites_sec)
    hindex = sum(c > i for i, c in enumerate(cites))
    hindex_first = sum(c > i for i, c in enumerate(cites_first))

    summary = (
        f"Metrics for Refereed Publications "
        f"(from \\href{{\\adsurl}}{{ADS}} as of \\textit{{{date.today()}}}) \\\\"
        f"count: {nref} --- citations: {ncitations} --- h-index: {hindex}"
    )
    print("-" * 32)
    print("Summary:")
    print(summary)

    summary_1st = (
        f" as First Author (count: {nfirst} --- citations: {ncitations_first})"
    )

    summary_2nd = (
        f" w/ Significant Contribution (count: {nsec} --- citations: {ncitations_sec})"
    )

    summary_co = (
        f" as Co-Author (count: {nref - nfirst - nsec} --- "
        f"citations: {ncitations - ncitations_first - ncitations_sec})"
    )
    file_list = [
        "summary.tex",
        "summary_1st.tex",
        "summary_2nd.tex",
        "summary_co.tex",
        "pubs_ref.tex",
        "pubs_ref_1st.tex",
        "pubs_ref_2nd.tex",
        "pubs_ref_co.tex",
        "pubs_arxiv.tex",
    ]
    data_list = [
        summary,
        summary_1st,
        summary_2nd,
        summary_co,
        refs,
        first_refs,
        sec_refs,
        other_refs,
        unrefs,
    ]
    for f, data in zip(file_list, data_list):
        with open(path.join(dirpath, f), "w") as fp:
            if f.startswith("pubs"):
                fp.write("\n\n".join(data))
            else:
                fp.write(data)

    # publications in specific periods
    refs, unrefs, first_refs, sec_refs, other_refs = get_paper_items(
        papers, periods=["2023-01-01", "2024-12-31"]
    )

    with open(path.join(dirpath, "pubs_ref_2023-2024.tex"), "w") as fp:
         fp.write("\n\n".join(refs))

    with open(path.join(dirpath, "pubs_arxiv_2023-2024.tex"), "w") as fp:
         fp.write("\n\n".join(unrefs))
