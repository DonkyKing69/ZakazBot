from datetime import datetime


def write_log(logs, from_file):
    for log in logs:
        print(f"{str(log)} \n")
    print("\nFrom file: " + from_file + "\n" + "Date-time: " + datetime.now().strftime("%Y-%m-%d %H-%M \n"))
    print("-" * 25 + '\n\n\n')


    # with open("log.txt", "a", encoding="utf-8") as f:
    #     for log in logs:
    #         f.write(f"{str(log)} \n")
    #     f.write("\nFrom file: " + from_file + "\n" + "Date-time: " + datetime.now().strftime("%Y-%m-%d %H-%M \n"))
    #     f.write("-" * 25 + '\n\n\n')