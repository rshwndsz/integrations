from goodreads.parser import parseArgs, getUpdatedLibrary


def test_library_update():
    args = parseArgs(["--books", "2", "--input", "./tests/test_input.csv"])
    df = getUpdatedLibrary(args.input, args.books)

    assert df.loc[0, "Title"] == "Shadow & Flame (Rime Chronicles, #2)"
    assert df.loc[0, "Author"] == "Mindee Arnett"
    genres = [
        "Fantasy",
        "Young Adult",
        "Young Adult > Young Adult Fantasy",
        "Romance",
        "Fantasy > Magic",
        "Fantasy > High Fantasy",
        "Romance > Fantasy Romance",
        "Audiobook",
        "Fiction",
        "Science Fiction Fantasy",
    ]
    assert df.loc[0, "Genres"] == ", ".join(genres)
    assert (
        df.loc[0, "Cover Image"]
        == "https://i.gr-assets.com/images/S/compressed.photo.goodreads.com/books/1539640135l/40042001.jpg"
    )

    assert df.loc[1, "Title"] == "Serpent & Dove (Serpent & Dove, #1)"
    assert df.loc[1, "Author"] == "Shelby Mahurin"
    genres = [
        "Fantasy",
        "Romance",
        "Young Adult",
        "Young Adult > Young Adult Fantasy",
        "Paranormal > Witches",
        "Fantasy > Magic",
        "Fiction",
        "Fantasy > Paranormal",
        "New Adult",
        "Audiobook",
    ]
    assert df.loc[1, "Genres"] == ", ".join(genres)
    assert (
        df.loc[1, "Cover Image"]
        == "https://i.gr-assets.com/images/S/compressed.photo.goodreads.com/books/1549476128l/40024139.jpg"
    )
