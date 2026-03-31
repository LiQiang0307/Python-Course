import random

def ask(prompt: str) -> str:
    return input(prompt).strip().lower()

def main():
    print("欢迎来到《命令行密室逃脱》！输入 help 查看指令。")
    hp = 3
    turns = 12
    bag = set()
    door_unlocked = False

    while turns > 0 and hp > 0 and not door_unlocked:
        # 顺序结构：显示状态 -> 读输入 -> 分支处理
        hint = "墙上有微弱的荧光字。" if "flashlight" in bag else "房间很暗，你看不清墙上的字。"
        print(f"\n回合剩余：{turns} | 生命：{hp} | 背包：{sorted(bag) or ['(空)']}")
        print(hint)

        cmd = ask("你要做什么？(look/take/use/roll/help/quit) > ")

        if cmd == "help":
            print("指令：look(观察) take(拿取) use(使用物品) roll(掷骰子) quit(退出)")
            continue  # 跳过本回合其余逻辑（不扣回合也可，这里演示 continue）
        elif cmd == "quit":
            print("你选择了退出。游戏结束。")
            break
        elif cmd == "look":
            print("你看到：桌子(table)、抽屉(drawer)、门(door)、角落(corner)。")
        elif cmd == "take":
            obj = ask("要拿什么？(flashlight/key/coin) > ")
            if obj in ("flashlight", "key", "coin"):
                if obj in bag:
                    print("你已经拿过了。")
                else:
                    bag.add(obj)
                    print(f"你获得了：{obj}")
            else:
                print("这里没有这个东西。")
                continue  # 无效输入，直接进入下一轮
        elif cmd == "use":
            item = ask("要使用什么？(flashlight/key/coin) > ")

            if item not in bag:
                print("你背包里没有这个。")
                continue

            if item == "flashlight":
                print("你打开手电筒，墙上写着：'3次机会，猜中数字 1~6 可开门。'")
            elif item == "coin":
                print("你把硬币塞进门旁的机器，机器吐出一张纸条：'失败会扣血，但别慌。'")
            elif item == "key":
                print("钥匙似乎能开门，但门锁需要先通过数字验证。")
            else:
                pass  # 预留：未来增加更多物品

        elif cmd == "roll":
            # for 循环：开锁 3 次机会
            if "key" not in bag:
                print("你想掷骰子挑战开锁，但你连钥匙都没有（需要 key）。")
                continue

            secret = random.randint(1, 6)
            print("门锁启动：你有 3 次机会猜 1~6 的数字。")

            for attempt in range(1, 4):
                guess_raw = ask(f"第 {attempt} 次猜测 > ")
                if not guess_raw.isdigit():
                    print("请输入数字 1~6。")
                    continue  # 本次机会不浪费？这里演示 continue：仍算一次循环，但不做比较
                guess = int(guess_raw)
                if not (1 <= guess <= 6):
                    print("范围必须是 1~6。")
                    continue

                if guess == secret:
                    print("咔哒！你猜对了，门锁解开！")
                    door_unlocked = True
                    break
                else:
                    hp -= 1
                    print("猜错了！门锁反噬扣 1 点生命。")

            else:
                # for-else：3 次都没 break（没成功）才会执行
                print("三次机会用尽，门锁暂时关闭。")

        else:
            # 未知指令：演示 pass（先不处理也不报错），但给提示
            pass
            print("我不认识这个指令。输入 help 查看可用指令。")
            continue

        # 回合减少放在末尾，确保流程清晰
        turns -= 1

    # 游戏结局（选择结构）
    if door_unlocked:
        ending = "你推开门，重见天日！" if hp > 0 else "你打开了门，但也倒下了（惨烈通关）。"
        print("\n通关！" + ending)
    elif hp <= 0:
        print("\n你体力耗尽，倒在门前。游戏失败。")
    else:
        print("\n时间耗尽，房间重新上锁。游戏失败。")

if __name__ == "__main__":
    main()