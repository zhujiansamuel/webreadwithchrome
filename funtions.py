import string, random



def generate_key(lenght):
    letter = string.ascii_letters
    return ''.join(random.choice(letter) for i in range(lenght))




