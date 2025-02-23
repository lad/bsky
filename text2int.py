'''Parse strings with textual representations of numbers into integers'''


def parse(text):
    '''Parse the given string and return the integer equivalent'''
    # Define a mapping of text numbers to integers
    number_map = {
        "zero": 0,
        "one": 1,
        "two": 2,
        "three": 3,
        "four": 4,
        "five": 5,
        "six": 6,
        "seven": 7,
        "eight": 8,
        "nine": 9,
        "ten": 10,
        "eleven": 11,
        "twelve": 12,
        "thirteen": 13,
        "fourteen": 14,
        "fifteen": 15,
        "sixteen": 16,
        "seventeen": 17,
        "eighteen": 18,
        "nineteen": 19,
        "twenty": 20,
        "thirty": 30,
        "forty": 40,
        "fifty": 50,
        "sixty": 60,
        "seventy": 70,
        "eighty": 80,
        "ninety": 90
    }

    # Split the input text into words
    words = text.lower().split()

    total = 0
    current = 0

    for word in words:
        if word in number_map:
            current += number_map[word]
        else:
            raise ValueError(f"Invalid number word: {word}")

    total += current
    return total


def test():
    '''Example usage'''
    numbers = [
        "sixty seven",
        "one",
        "two",
        "eleven",
        "twenty",
        "twenty one",
        "ninety nine",
        "forty five"
    ]

    for number in numbers:
        try:
            result = parse(number)
            print(f"{number} -> {result}")
        except ValueError as e:
            print(e)


if __name__ == '__main__':
    test()
