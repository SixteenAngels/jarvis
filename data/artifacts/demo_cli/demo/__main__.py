import argparse
def main():
    parser = argparse.ArgumentParser(prog='demo')
    parser.add_argument('--name', default='world')
    args = parser.parse_args()
    print(f'Hello, {args.name}!')
if __name__ == '__main__':
    main()
