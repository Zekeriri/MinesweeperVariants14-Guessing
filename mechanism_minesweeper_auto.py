import pyautogui
import time
import keyboard
import threading

# ====== 线程监听 S 键强制退出 ======
should_exit = False

def listen_for_exit():
    global should_exit
    while True:
        if keyboard.is_pressed('s'):
            should_exit = True
            print("\n[日志] 检测到 S 键，准备终止脚本...")
            break
        time.sleep(0.05)

exit_thread = threading.Thread(target=listen_for_exit, daemon=True)
exit_thread.start()
# ==================================

def get_grid_centers(top_left, bottom_right, cols, rows):
    """计算每个格子的中心坐标"""
    x0, y0 = top_left
    x1, y1 = bottom_right
    cell_width = (x1 - x0) / cols
    cell_height = (y1 - y0) / rows
    centers = []
    for row in range(rows):
        for col in range(cols):
            x = int(x0 + col * cell_width + cell_width / 2)
            y = int(y0 + row * cell_height + cell_height / 2)
            centers.append((x, y))
    return centers

def check_fail_window(point):
    """极速检测失败窗口：只要不是黑色就判定为失败"""
    x, y = point
    color = pyautogui.pixel(x, y)
    return color != (0, 0, 0)

def fast_click(x, y, button='left', delay_after=0.05):
    """快速点击 - 加入适当延迟让游戏反应"""
    pyautogui.mouseDown(x, y, button=button)
    pyautogui.mouseUp(x, y, button=button)
    if delay_after > 0:
        safe_sleep(delay_after)

def replay_steps_fast(centers, steps, click_delay=0.03):
    """快速回放 - 加入最小延迟"""
    for idx, op in steps:
        if should_exit:
            break
        x, y = centers[idx]
        fast_click(x, y, button=op, delay_after=click_delay)

def format_time(seconds):
    """格式化时间显示"""
    if seconds < 60:
        return f"{seconds:.2f}秒"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}分{secs:.2f}秒"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours}小时{minutes}分{secs:.2f}秒"

def safe_sleep(seconds):
    """可被 S 键中断的 sleep"""
    interval = 0.05
    elapsed = 0
    while elapsed < seconds:
        if should_exit:
            break
        time.sleep(interval)
        elapsed += interval

def main():
    # ====== 请根据实际情况修改以下参数 ======
    x0 = 744  # 左上角x
    y0 = 377  # 左上角y
    x1 = 1176  # 右下角x
    y1 = 809  # 右下角y
    cols = 5  # 列数
    rows = 5  # 行数
    fail_x = 1648  # 检查失败窗口的x
    fail_y = 229  # 检查失败窗口的y
    reset_x = 1335  # 重置按钮x
    reset_y = 811  # 重置按钮y

    # 性能调优参数
    click_delay = 1    # 每次点击后的延迟（秒）
    replay_delay = 1   # 回放时每步的延迟（秒）
    reset_wait = 1     # 重置后的等待时间（秒）
    fail_check_delay = 0.05  # 检查失败窗口前的等待时间（秒）
    # =========================================

    pyautogui.PAUSE = 0
    pyautogui.FAILSAFE = False

    print("\n=== 机关扫雷智能穷举脚本（详细日志模式） ===")
    print("请切换到机关扫雷界面，3秒后自动开始！（按 S 可随时终止）")
    for i in range(3, 0, -1):
        if should_exit:
            print("\n检测到 S 键，程序终止。")
            return
        print(f"{i}...")
        safe_sleep(1)

    start_time = time.time()
    print(f"\n开始时间：{time.strftime('%H:%M:%S', time.localtime(start_time))}")
    print("开始智能穷举...")

    centers = get_grid_centers((x0, y0), (x1, y1), cols, rows)
    ops = ['left', 'right']
    total = len(centers)
    steps = []
    used = set()
    attempt_count = 0
    step_attempts = 0

    while len(steps) < total and not should_exit:
        found = False
        for idx in range(total):
            if should_exit:
                break
            if idx in used:
                continue
            for op in ops:
                if should_exit:
                    break

                attempt_count += 1
                step_attempts += 1

                # 日志：准备回放
                print(f"\n[日志] 第{attempt_count}次尝试：回放已知步骤...")
                replay_steps_fast(centers, steps, replay_delay)

                # 日志：尝试当前格子
                row = idx // cols + 1
                col = idx % cols + 1
                op_name = "左键" if op == "left" else "右键"
                print(f"[日志] 尝试第{row}行第{col}列 - {op_name}")

                x, y = centers[idx]
                fast_click(x, y, button=op, delay_after=click_delay)

                safe_sleep(fail_check_delay)

                if should_exit:
                    break

                if check_fail_window((fail_x, fail_y)):
                    print(f"[日志] 失败！检测到失败窗口，准备重置...")
                    fast_click(reset_x, reset_y, delay_after=reset_wait)
                    # 等待窗口完全关闭
                    wait_cnt = 0
                    while check_fail_window((fail_x, fail_y)):
                        if should_exit:
                            break
                        time.sleep(0.01)
                        wait_cnt += 1
                        if wait_cnt > 100:
                            print("[警告] 失败窗口长时间未关闭，可能出现异常。")
                            break
                    print(f"[日志] 重置完成，继续下一次尝试。")
                    continue
                else:
                    current_time = time.time()
                    elapsed_time = current_time - start_time
                    print(
                        f"[日志] ✓ 成功！第{len(steps) + 1}步：第{row}行第{col}列-{op_name} (本步尝试{step_attempts}次, 总用时{format_time(elapsed_time)})")
                    steps.append((idx, op))
                    used.add(idx)
                    step_attempts = 0
                    found = True
                    break
            if found or should_exit:
                break

    # 结束计时
    end_time = time.time()
    elapsed_time = end_time - start_time

    print("\n" + "=" * 60)
    if should_exit:
        print("⚠️  检测到 S 键，程序已终止。")
    else:
        print("🎉 全部操作完成！")
    print(f"开始时间：{time.strftime('%H:%M:%S', time.localtime(start_time))}")
    print(f"结束时间：{time.strftime('%H:%M:%S', time.localtime(end_time))}")
    print(f"总用时：{format_time(elapsed_time)}")
    print(f"总尝试次数：{attempt_count}")
    print(f"平均每步用时：{format_time(elapsed_time / (len(steps) if steps else 1))}")
    print(f"平均每步尝试次数：{attempt_count / (len(steps) if steps else 1):.1f}")
    print("=" * 60)

    print("\n📋 完整操作序列：")
    for i, (idx, op) in enumerate(steps, 1):
        row = idx // cols + 1
        col = idx % cols + 1
        op_name = "左键" if op == "left" else "右键"
        print(f"第{i:2d}步：第{row}行第{col}列 - {op_name}")

    print(f"\n🔧 性能参数设置：")
    print(f"   点击延迟：{click_delay}秒")
    print(f"   回放延迟：{replay_delay}秒")
    print(f"   重置等待：{reset_wait}秒")
    print(f"   失败检查延迟：{fail_check_delay}秒")

    print(f"\n按任意键退出程序...")
    keyboard.read_event()

if __name__ == "__main__":
    main()
