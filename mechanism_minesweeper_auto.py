import pyautogui
import time
import keyboard
import threading

LOG_CLICK = True  # 日志开关

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


def get_grid_centers(top_left, bottom_right, cols, rows):
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
    x, y = point
    color = pyautogui.pixel(x, y)
    return color != (0, 0, 0)


def check_win_point(win_x, win_y, win_color=(255, 255, 0)):
    color = pyautogui.pixel(win_x, win_y)
    return color == win_color


def fast_click(x, y, button='left', delay_after=0.05, log_info=None):
    if LOG_CLICK and log_info:
        print(f"[点击日志] {log_info}")
    pyautogui.mouseDown(x, y, button=button)
    pyautogui.mouseUp(x, y, button=button)
    if delay_after > 0:
        safe_sleep(delay_after)


def replay_steps_fast(centers, steps, cols, click_delay=0.03):
    for idx, op in steps:
        if should_exit:
            break
        x, y = centers[idx]
        row = idx // cols + 1
        col = idx % cols + 1
        op_name = "左键" if op == "left" else "右键"
        log_info = f"回放步骤：第{row}行第{col}列 - {op_name}"
        fast_click(x, y, button=op, delay_after=click_delay, log_info=log_info)


def format_time(seconds):
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
    interval = 0.05
    elapsed = 0
    while elapsed < seconds:
        if should_exit:
            break
        time.sleep(interval)
        elapsed += interval


def single_level_solve(centers, cols, total, fail_x, fail_y, reset_x, reset_y, click_delay, replay_delay, reset_wait,
                       fail_check_delay, win_x, win_y, next_button_x, next_button_y):
    steps = []
    used = set()
    tried_ops = set()
    step_attempts = 0
    attempt_count = 0
    need_replay = False

    level_start_time = time.time()
    while not should_exit:
        if len(steps) >= total:
            break
        if need_replay:
            print(f"\n[日志] 重置后需要回放{len(steps)}步...")
            replay_steps_fast(centers, steps, cols, replay_delay)
            need_replay = False
        found = False
        all_tried = True
        for idx in range(total):
            if should_exit:
                break
            if idx in used:
                continue
            for op in ['left', 'right']:
                if should_exit:
                    break
                if (idx, op) in tried_ops:
                    continue
                all_tried = False
                attempt_count += 1
                step_attempts += 1
                row = idx // cols + 1
                col = idx % cols + 1
                op_name = "左键" if op == "left" else "右键"
                print(f"[日志] 尝试第{row}行第{col}列 - {op_name} (本关第{attempt_count}次尝试)")
                x, y = centers[idx]
                fast_click(x, y, button=op, delay_after=click_delay,
                           log_info=f"本次尝试：第{row}行第{col}列 - {op_name}")
                safe_sleep(fail_check_delay)
                tried_ops.add((idx, op))
                if should_exit:
                    break
                if check_fail_window((fail_x, fail_y)):
                    print(f"[日志] 失败！检测到失败窗口，准备重置...")
                    fast_click(reset_x, reset_y, delay_after=reset_wait, log_info="点击重置按钮")
                    center_x, center_y = centers[total // 2]
                    pyautogui.moveTo(center_x, center_y)
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
                    need_replay = True
                    break
                else:
                    current_time = time.time()
                    elapsed_time = current_time - level_start_time
                    print(
                        f"[日志] ✓ 成功！第{len(steps) + 1}步：第{row}行第{col}列-{op_name} (本步尝试{step_attempts}次, 本关用时{format_time(elapsed_time)})")
                    steps.append((idx, op))
                    used.add(idx)
                    tried_ops.clear()
                    step_attempts = 0
                    found = True
                    # ===== 检查通关点颜色，若已通关则返回 =====
                    if check_win_point(win_x, win_y):
                        print(f"[日志] 检测到通关颜色 (255,255,0)，点击通关点并进入下一关！")
                        pyautogui.click(win_x, win_y)
                        safe_sleep(0.5)
                        pyautogui.click(next_button_x, next_button_y)
                        safe_sleep(0.5)
                        return steps, attempt_count, time.time() - level_start_time
                    break
            if found or need_replay or should_exit:
                break
        if all_tried:
            print("\n[日志] 所有格子的所有操作都已尝试，未能解开，脚本自动结束本关。")
            break
    return steps, attempt_count, time.time() - level_start_time


def main():
    # ====== 参数设置 ======
    x0 = 744
    y0 = 377
    x1 = 1176
    y1 = 809
    cols = 5
    rows = 5
    fail_x = 1648
    fail_y = 229    # 右上角的×
    reset_x = 1335
    reset_y = 811
    win_x = 1500  # 通关检测点x
    win_y = 65  # 通关检测点y    黄色的⏩或✅
    next_button_x = 1024
    next_button_y = 820 # 下一关按钮位置

    click_delay = 0.05
    replay_delay = 0.03
    reset_wait = 0.1
    fail_check_delay = 0.05
    total_levels = 100  # ====== 需要连续通关的关数 ======
    # ====================

    pyautogui.PAUSE = 0
    pyautogui.FAILSAFE = False

    print("\n=== 14种扫雷变体试错法脚本（多关自动模式） ===")
    print(f"将自动连续通关 {total_levels} 关！请切换到游戏界面，3秒后自动开始！（按 S 可随时终止）")
    for i in range(3, 0, -1):
        if should_exit:
            print("\n检测到 S 键，程序终止。")
            return
        print(f"{i}...")
        safe_sleep(1)

    all_level_info = []
    total_start_time = time.time()
    centers = get_grid_centers((x0, y0), (x1, y1), cols, rows)
    total = len(centers)

    for level in range(1, total_levels + 1):
        if should_exit:
            break
        print(f"\n{'=' * 30}\n[关卡] 第 {level} 关开始\n{'=' * 30}")
        steps, attempts, used_time = single_level_solve(
            centers, cols, total, fail_x, fail_y, reset_x, reset_y,
            click_delay, replay_delay, reset_wait, fail_check_delay,
            win_x, win_y, next_button_x, next_button_y)
        all_level_info.append((steps, attempts, used_time))
        if should_exit:
            print(f"\n[日志] 检测到 S 键，提前退出")
            break
        print(f"\n[关卡] 第 {level} 关完成！用时：{format_time(used_time)}，尝试次数：{attempts}，步数：{len(steps)}")
        safe_sleep(2)  # 每关之间可适当等待

    total_end_time = time.time()
    print("\n" + "=" * 60)
    print(f"全部关卡已完成或中断，总用时：{format_time(total_end_time - total_start_time)}")
    for i, (steps, attempts, used_time) in enumerate(all_level_info, 1):
        print(f"\n【第{i}关】用时：{format_time(used_time)}，尝试次数：{attempts}，步数：{len(steps)}")
    print("=" * 60)
    print(f"\n按任意键退出程序...")
    keyboard.read_event()


if __name__ == "__main__":
    main()
