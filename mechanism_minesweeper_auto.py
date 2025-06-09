import pyautogui
import time
import keyboard
import threading

# ====== 日志开关 ======
LOG_CLICK = True  # 改为 False 即可关闭所有点击日志
# =====================

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


def main():
    # ====== 请根据实际情况修改以下参数 ======
    x0 = 744
    y0 = 377
    x1 = 1176
    y1 = 809
    cols = 5
    rows = 5
    fail_x = 1648
    fail_y = 229
    reset_x = 1335
    reset_y = 811

    click_delay = 0.05
    replay_delay = 0.03
    reset_wait = 0.1
    fail_check_delay = 0.05
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
    tried_ops = set()
    need_replay = False  # 新增：是否需要回放步骤的标志

    while len(steps) < total and not should_exit:
        # 只在需要时回放步骤（重置后）
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
            for op in ops:
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
                print(f"[日志] 尝试第{row}行第{col}列 - {op_name} (总第{attempt_count}次尝试)")

                # 直接点击当前格子（不先回放所有步骤）
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
                    need_replay = True  # 标记需要回放
                    break  # 跳出操作循环
                else:
                    current_time = time.time()
                    elapsed_time = current_time - start_time
                    print(
                        f"[日志] ✓ 成功！第{len(steps) + 1}步：第{row}行第{col}列-{op_name} (本步尝试{step_attempts}次, 总用时{format_time(elapsed_time)})")
                    steps.append((idx, op))
                    used.add(idx)
                    tried_ops.clear()
                    step_attempts = 0
                    found = True
                    break  # 跳出操作循环
            if found or need_replay or should_exit:
                break  # 跳出格子循环
        if all_tried:
            print("\n[日志] 所有格子的所有操作都已尝试，未能解开，脚本自动结束。")
            break

    end_time = time.time()
    elapsed_time = end_time - start_time

    print("\n" + "=" * 60)
    if should_exit:
        print("⚠️  检测到 S 键，程序已终止。")
    elif len(steps) < total:
        print("❌ 未能解开机关，所有操作都已尝试。")
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