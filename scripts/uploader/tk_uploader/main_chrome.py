# -*- coding: utf-8 -*-
import re
from datetime import datetime
import time
from pathlib import Path

from playwright.async_api import Playwright, async_playwright
import os
import asyncio

from conf import LOCAL_CHROME_PATH, USE_CDP_CHROME, CHROME_CDP_URL, LOCAL_CHROME_USER_DATA_DIR
from uploader.tk_uploader.tk_config import Tk_Locator
from utils.base_social_media import set_init_script
from utils.files_times import get_absolute_path
from utils.log import tiktok_logger


async def cookie_auth(account_file):
    async with async_playwright() as playwright:
        if LOCAL_CHROME_PATH:
            browser = await playwright.chromium.launch(headless=True, executable_path=LOCAL_CHROME_PATH)
        else:
            browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context(storage_state=account_file)
        context = await set_init_script(context)
        # 创建一个新的页面
        page = await context.new_page()
        # 访问指定的 URL
        await page.goto("https://www.tiktok.com/tiktokstudio/upload?lang=en")
        await page.wait_for_load_state('networkidle')
        try:
            # 选择所有的 select 元素
            select_elements = await page.query_selector_all('select')
            for element in select_elements:
                class_name = await element.get_attribute('class')
                # 使用正则表达式匹配特定模式的 class 名称
                if re.match(r'tiktok-.*-SelectFormContainer.*', class_name):
                    tiktok_logger.error("[+] cookie expired")
                    return False
            tiktok_logger.success("[+] cookie valid")
            return True
        except:
            tiktok_logger.success("[+] cookie valid")
            return True


async def tiktok_setup(account_file, handle=False):
    account_file = get_absolute_path(account_file, "tk_uploader")
    if not os.path.exists(account_file) or not await cookie_auth(account_file):
        if not handle:
            return False
        tiktok_logger.info('[+] cookie file is not existed or expired. Now open the browser auto. Please login with your way(gmail phone, whatever, the cookie file will generated after login')
        await get_tiktok_cookie(account_file)
    return True


async def get_tiktok_cookie(account_file):
    async with async_playwright() as playwright:
        options = {
            'args': [
                '--lang en-GB',
            ],
            'headless': False,  # Set headless option here
        }
        if LOCAL_CHROME_PATH:
            browser = await playwright.chromium.launch(executable_path=LOCAL_CHROME_PATH, **options)
        else:
            browser = await playwright.chromium.launch(**options)
        # Setup context however you like.
        context = await browser.new_context()  # Pass any options
        context = await set_init_script(context)
        # Pause the page, and start recording manually.
        page = await context.new_page()
        await page.goto("https://www.tiktok.com/login?lang=en")
        await page.pause()
        # 点击调试器的继续，保存cookie
        await context.storage_state(path=account_file)


class TiktokVideo(object):
    def __init__(self, title, file_path, tags, publish_date, account_file, thumbnail_path=None, is_ai_content=None):
        self.title = title
        self.file_path = file_path
        self.tags = tags
        self.publish_date = publish_date
        self.thumbnail_path = thumbnail_path
        self.account_file = account_file
        self.local_executable_path = LOCAL_CHROME_PATH
        self.locator_base = None
        self.is_ai_content = is_ai_content

    async def set_schedule_time(self, page, publish_date):
        schedule_input_element = self.locator_base.get_by_label('Schedule')
        await schedule_input_element.wait_for(state='visible')  # 确保按钮可见

        await schedule_input_element.click(force=True)
        if await self.locator_base.locator('div.TUXButton-content >> text=Allow').count():
            await self.locator_base.locator('div.TUXButton-content >> text=Allow').click()

        scheduled_picker = self.locator_base.locator('div.scheduled-picker')
        await scheduled_picker.locator('div.TUXInputBox').nth(1).click()

        calendar_month = await self.locator_base.locator(
            'div.calendar-wrapper span.month-title').inner_text()

        n_calendar_month = datetime.strptime(calendar_month, '%B').month

        schedule_month = publish_date.month

        if n_calendar_month != schedule_month:
            if n_calendar_month < schedule_month:
                arrow = self.locator_base.locator('div.calendar-wrapper span.arrow').nth(-1)
            else:
                arrow = self.locator_base.locator('div.calendar-wrapper span.arrow').nth(0)
            await arrow.click()

        # day set
        valid_days_locator = self.locator_base.locator(
            'div.calendar-wrapper span.day.valid')
        valid_days = await valid_days_locator.count()
        for i in range(valid_days):
            day_element = valid_days_locator.nth(i)
            text = await day_element.inner_text()
            if text.strip() == str(publish_date.day):
                await day_element.click()
                break
        # time set
        await scheduled_picker.locator('div.TUXInputBox').nth(0).click()

        hour_str = publish_date.strftime("%H")
        correct_minute = int(publish_date.minute / 5)
        minute_str = f"{correct_minute:02d}"

        hour_selector = f"span.tiktok-timepicker-left:has-text('{hour_str}')"
        minute_selector = f"span.tiktok-timepicker-right:has-text('{minute_str}')"

        # pick hour first
        await page.wait_for_timeout(1000)  # 等待500毫秒
        await self.locator_base.locator(hour_selector).click()
        # click time button again
        await page.wait_for_timeout(1000)  # 等待500毫秒
        # pick minutes after
        await self.locator_base.locator(minute_selector).click()

        # click title to remove the focus.
        # await self.locator_base.locator("h1:has-text('Upload video')").click()

    async def handle_upload_error(self, page):
        tiktok_logger.info("video upload error retrying.")
        select_file_button = self.locator_base.locator('button[aria-label="Select file"]')
        async with page.expect_file_chooser() as fc_info:
            await select_file_button.click()
        file_chooser = await fc_info.value
        await file_chooser.set_files(self.file_path)

    async def upload(self, playwright: Playwright) -> None:
        browser = None
        context = None
        if USE_CDP_CHROME:
            try:
                browser = await playwright.chromium.connect_over_cdp(CHROME_CDP_URL)
                if browser.contexts:
                    context = browser.contexts[0]
                else:
                    context = await browser.new_context()
            except Exception:
                pass
        if context is None and LOCAL_CHROME_USER_DATA_DIR:
            try:
                if self.local_executable_path and os.path.isfile(self.local_executable_path) and os.access(self.local_executable_path, os.X_OK):
                    context = await playwright.chromium.launch_persistent_context(LOCAL_CHROME_USER_DATA_DIR, executable_path=self.local_executable_path, headless=False, channel="chrome")
                else:
                    context = await playwright.chromium.launch_persistent_context(LOCAL_CHROME_USER_DATA_DIR, headless=False, channel="chrome")
                browser = context.browser
            except Exception:
                pass
        if context is None:
            launch_kwargs = {"headless": False}
            path = (self.local_executable_path or "").strip()
            try:
                if path and os.path.isfile(path) and os.access(path, os.X_OK):
                    launch_kwargs["executable_path"] = path
                else:
                    tiktok_logger.info("[browser] LOCAL_CHROME_PATH 未设置或不可执行，使用默认浏览器/Chrome 渠道")
                    launch_kwargs["channel"] = "chrome"
            except Exception:
                pass
            browser = await playwright.chromium.launch(**launch_kwargs)
            context = await browser.new_context(storage_state=f"{self.account_file}")
        # context = await set_init_script(context)
        page = await context.new_page()

        # change language to eng first
        await self.change_language(page)
        await page.goto("https://www.tiktok.com/tiktokstudio/upload")
        tiktok_logger.info(f'[+]Uploading-------{self.title}.mp4')

        await page.wait_for_url("https://www.tiktok.com/tiktokstudio/upload", timeout=20000)

        # 等待页面加载完成
        await page.wait_for_load_state('networkidle', timeout=30000)
        tiktok_logger.info("Page load state: networkidle")

        try:
            await self.wait_for_upload_surface(page)
        except Exception as exc:
            tiktok_logger.error(f"Upload surface not detected in time: {exc}")
            await self.save_debug_artifacts(page, base_name='debug_upload_page')
            raise Exception("Failed to load TikTok upload page") from exc

        await self.choose_base_locator(page)

        # 添加额外延迟确保页面完全加载
        await page.wait_for_timeout(2000)

        upload_button = self.locator_base.locator(
            'button:has-text("Select video"):visible')

        try:
            await upload_button.wait_for(state='visible', timeout=30000)  # 增加等待时间
            tiktok_logger.info("Upload button is visible")
        except Exception as e:
            tiktok_logger.error(f"Upload button not found: {e}")
            # 尝试查找其他可能的按钮
            alternative_button = self.locator_base.locator('button[aria-label="Select video"]')
            if await alternative_button.count():
                tiktok_logger.info("Found alternative upload button")
                upload_button = alternative_button
            else:
                # 截图以帮助调试
                try:
                    await page.screenshot(path='debug_button_missing.png')
                    tiktok_logger.info("Screenshot saved to debug_button_missing.png")
                except:
                    pass
                raise Exception("Upload button not found")

        async with page.expect_file_chooser() as fc_info:
            await upload_button.click()
        file_chooser = await fc_info.value
        await file_chooser.set_files(self.file_path)

        await self.add_title_tags(page)
        # detect upload status
        await self.detect_upload_status(page)
        if self.thumbnail_path:
            tiktok_logger.info(f'[+] Uploading thumbnail file {self.title}.png')
            await self.upload_thumbnails(page)
        await self.configure_ai_generated_flag(page)

        if self.publish_date != 0:
            await self.set_schedule_time(page, self.publish_date)

        await self.click_publish(page)
        tiktok_logger.success(f"video_id: {await self.get_last_video_id(page)}")

        await context.storage_state(path=f"{self.account_file}")
        tiktok_logger.info('  [-] update cookie！')
        await asyncio.sleep(2)  # close delay for look the video status
        # close all
        try:
            await context.close()
        except Exception:
            pass
        try:
            await browser.close()
        except Exception:
            pass

    async def add_title_tags(self, page):
        await self.ensure_modal_closed(page, wait_seconds=5)
        editor_locator = self.locator_base.locator('div.public-DraftEditor-content')
        await editor_locator.click()

        await page.keyboard.press("End")

        await page.keyboard.press("Control+A")

        await page.keyboard.press("Delete")

        await page.keyboard.press("End")

        await page.wait_for_timeout(1000)  # 等待1秒

        await page.keyboard.insert_text(self.title)
        await page.wait_for_timeout(1000)  # 等待1秒
        await page.keyboard.press("End")

        await page.keyboard.press("Enter")

        # tag part
        for index, tag in enumerate(self.tags, start=1):
            tiktok_logger.info("Setting the %s tag" % index)
            await page.keyboard.press("End")
            await page.wait_for_timeout(1000)  # 等待1秒
            await page.keyboard.insert_text("#" + tag + " ")
            await page.keyboard.press("Space")
            await page.wait_for_timeout(1000)  # 等待1秒

            await page.keyboard.press("Backspace")
            await page.keyboard.press("End")

    async def upload_thumbnails(self, page):
        await self.locator_base.locator(".cover-container").click()
        await self.locator_base.locator(".cover-edit-container >> text=Upload cover").click()
        async with page.expect_file_chooser() as fc_info:
            await self.locator_base.locator(".upload-image-upload-area").click()
            file_chooser = await fc_info.value
            await file_chooser.set_files(self.thumbnail_path)
        await self.locator_base.locator('div.cover-edit-panel:not(.hide-panel)').get_by_role(
            "button", name="Confirm").click()
        await page.wait_for_timeout(3000)  # wait 3s, fix it later

    async def configure_ai_generated_flag(self, page):
        if self.is_ai_content is None:
            return
        try:
            await self.expand_advanced_settings(page)
            await self.set_ai_generated_switch(page, bool(self.is_ai_content))
        except Exception as exc:
            tiktok_logger.warning(f"[+] configure AI content flag failed: {exc}")

    async def expand_advanced_settings(self, page):
        if not self.locator_base:
            return False
        container = self.locator_base.locator('[data-e2e="advanced_settings_container"]')
        if not await container.count():
            tiktok_logger.warning("[+] advanced settings container not found")
            return False
        try:
            await container.first.scroll_into_view_if_needed()
        except Exception:
            pass
        class_attr = (await container.first.get_attribute("class") or "").lower()
        if "collapsed" not in class_attr:
            return True
        toggle = container.locator(r"text=/显示更多|show\s*more/i").first
        if not await toggle.count():
            toggle = container.locator('.more-btn').first
        if not await toggle.count():
            tiktok_logger.warning("[+] show-more button for advanced settings not found")
            return False
        await toggle.click()
        for _ in range(5):
            await page.wait_for_timeout(200)
            class_attr = (await container.first.get_attribute("class") or "").lower()
            if "collapsed" not in class_attr:
                return True
        tiktok_logger.warning("[+] advanced settings still collapsed after clicking show more")
        return False

    async def set_ai_generated_switch(self, page, enable_flag):
        if not self.locator_base:
            return
        container = self.locator_base.locator('[data-e2e="aigc_container"]')
        if not await container.count():
            tiktok_logger.warning("[+] AI content switch container not found")
            return
        switch_root = container.locator('[data-layout="switch-root"]').first
        if not await switch_root.count():
            switch_root = container.locator('.switch').first
        current_state = None
        state_holder = container.locator('[data-state]').first
        if await state_holder.count():
            raw_state = (await state_holder.get_attribute('data-state') or '').lower()
            if raw_state:
                current_state = raw_state == 'checked'
        if current_state is None:
            aria_switch = container.get_by_role("switch").first
            if await aria_switch.count():
                aria_state = (await aria_switch.get_attribute("aria-checked") or "").lower()
                if aria_state:
                    current_state = aria_state == 'true'
        if current_state is None:
            current_state = False
        if current_state == enable_flag or not await switch_root.count():
            return
        await switch_root.click()
        await page.wait_for_timeout(300)

        # 处理AI内容确认模态框
        await self.handle_ai_content_modal(page, enable_flag)

    async def handle_ai_content_modal(self, page, enable_flag: bool):
        """处理AI内容确认模态框"""
        try:
            # 等待模态框出现（如果有的话）
            modal = page.locator('.TUXModal.common-modal[role="dialog"]')
            if not await modal.count():
                modal = page.locator('.TUXModal')

            # 检查模态框是否出现，最多等待2秒
            try:
                await modal.wait_for(state='visible', timeout=2000)
            except Exception:
                # 没有模态框出现，直接返回
                tiktok_logger.info("[+] No AI content modal appeared")
                return

            tiktok_logger.info("[+] AI content confirmation modal detected")

            if enable_flag:
                # 如果是开启AI内容，点击 "Turn on" 按钮
                # 优先使用 get_by_role 定位按钮
                turn_on_button = page.get_by_role("button", name="Turn on")
                if not await turn_on_button.count():
                    # 备用方案1：使用 data-type 和文本组合
                    turn_on_button = page.locator('button[data-type="primary"]:has-text("Turn on")')
                if not await turn_on_button.count():
                    # 备用方案2：仅使用文本
                    turn_on_button = page.locator('button:has-text("Turn on")')

                if await turn_on_button.count():
                    await turn_on_button.click()
                    tiktok_logger.success("[+] Clicked 'Turn on' button in AI content modal")
                    await page.wait_for_timeout(500)
                else:
                    tiktok_logger.warning("[+] 'Turn on' button not found in modal")
            else:
                # 如果是关闭AI内容，点击 "Not now" 按钮（通常不会出现这种情况）
                not_now_button = page.get_by_role("button", name="Not now")
                if not await not_now_button.count():
                    not_now_button = page.locator('button[data-type="neutral"]:has-text("Not now")')
                if not await not_now_button.count():
                    not_now_button = page.locator('button:has-text("Not now")')

                if await not_now_button.count():
                    await not_now_button.click()
                    tiktok_logger.info("[+] Clicked 'Not now' button in AI content modal")
                    await page.wait_for_timeout(500)
                else:
                    tiktok_logger.warning("[+] 'Not now' button not found in modal")

            # 等待模态框消失
            try:
                await modal.wait_for(state='hidden', timeout=3000)
                tiktok_logger.success("[+] AI content modal closed successfully")
            except Exception:
                tiktok_logger.warning("[+] Modal did not close within timeout")

        except Exception as exc:
            tiktok_logger.warning(f"[+] handle AI content modal failed: {exc}")

    async def verify_ai_content_flag(self, page):
        """在发布前验证 AI 内容标记是否正确设置"""
        if not self.locator_base:
            return
        try:
            # 先确保高级设置已展开
            await self.expand_advanced_settings(page)

            container = self.locator_base.locator('[data-e2e="aigc_container"]')
            if not await container.count():
                tiktok_logger.warning("[+] AI content switch container not found during verification")
                return

            # 获取当前开关状态
            current_state = None
            state_holder = container.locator('[data-state]').first
            if await state_holder.count():
                raw_state = (await state_holder.get_attribute('data-state') or '').lower()
                if raw_state:
                    current_state = raw_state == 'checked'

            if current_state is None:
                aria_switch = container.get_by_role("switch").first
                if await aria_switch.count():
                    aria_state = (await aria_switch.get_attribute("aria-checked") or "").lower()
                    if aria_state:
                        current_state = aria_state == 'true'

            if current_state is None:
                current_state = False

            expected_state = bool(self.is_ai_content)

            # 如果状态不匹配，重新设置
            if current_state != expected_state:
                tiktok_logger.warning(f"[+] AI content flag mismatch! Current: {current_state}, Expected: {expected_state}")
                await self.set_ai_generated_switch(page, expected_state)
                tiktok_logger.success(f"[+] AI content flag corrected to: {expected_state}")
            else:
                tiktok_logger.success(f"[+] AI content flag verified: {current_state}")

        except Exception as exc:
            tiktok_logger.warning(f"[+] verify AI content flag failed: {exc}")

    async def change_language(self, page):
        # 语言切换流程如果失败无需阻塞上传，增加容错
        try:
            tiktok_logger.info("Starting language switch to English...")
            await page.goto("https://www.tiktok.com")
            await page.wait_for_load_state('domcontentloaded', timeout=15000)

            more_menu = page.locator('[data-e2e="nav-more-menu"]')
            await more_menu.wait_for(state='visible', timeout=10000)
            text = (await more_menu.text_content() or "").strip()

            if text and text.lower().startswith("more"):
                tiktok_logger.info("Page is already in English")
                return

            tiktok_logger.info("Switching to English language...")
            await more_menu.click()

            language_entry = page.locator('[data-e2e="language-select"]')
            await language_entry.wait_for(state='visible', timeout=5000)
            await language_entry.click()

            english_option = page.locator('#creator-tools-selection-menu-header').locator("text=English (US)")
            await english_option.wait_for(state='visible', timeout=5000)
            await english_option.click()

            tiktok_logger.success("Language switched to English successfully")
        except Exception as exc:
            tiktok_logger.warning(f"[+] skip language switch: {exc}")

    async def wait_for_video_check(self):
        """等待视频检查完成，只有当 data-show="true" 时才能发布"""
        tiktok_logger.info("  [-] waiting for video content check...")
        max_wait_time = 120  # 最多等待120秒
        start_time = time.time()

        while True:
            try:
                # 检查是否有状态结果显示
                status_result = self.locator_base.locator('div.status-result[data-show="true"]')

                if await status_result.count():
                    # 检查是否是成功状态
                    is_success = await status_result.locator('.status-success').count() > 0
                    if is_success:
                        tiktok_logger.success("  [-] video content check passed!")
                        return True
                    else:
                        # 可能是警告或错误状态
                        status_text = await status_result.locator('.status-tip').text_content() if await status_result.locator('.status-tip').count() else "Unknown status"
                        tiktok_logger.warning(f"  [-] video check status: {status_text}")
                        # 即使有警告，也继续发布
                        return True

                # 检查是否超时
                if time.time() - start_time > max_wait_time:
                    tiktok_logger.warning("  [-] video check timeout, proceeding anyway...")
                    return False

                await asyncio.sleep(2)
            except Exception as e:
                tiktok_logger.warning(f"  [-] error while checking video status: {e}")
                # 如果超时，继续发布
                if time.time() - start_time > max_wait_time:
                    return False
                await asyncio.sleep(2)

    async def click_publish(self, page):
        success_flag_div = 'div.common-modal-confirm-modal'
        while True:
            try:
                await self.ensure_modal_closed(page, wait_seconds=3)

                # 等待视频检查完成
                await self.wait_for_video_check()

                # 在发布前最后确认 AI 内容标记设置
                if self.is_ai_content is not None:
                    tiktok_logger.info("  [-] verifying AI content flag before publish...")
                    await self.verify_ai_content_flag(page)

                publish_button = self.locator_base.locator('div.button-group button').nth(0)
                if await publish_button.count():
                    await publish_button.click()
                    await self.ensure_modal_closed(page, wait_seconds=5)

                await page.wait_for_url("https://www.tiktok.com/tiktokstudio/content",  timeout=3000)
                tiktok_logger.success("  [-] video published success")
                break
            except Exception as e:
                tiktok_logger.exception(f"  [-] Exception: {e}")
                tiktok_logger.info("  [-] video publishing")
                await asyncio.sleep(0.5)

    async def get_last_video_id(self, page):
        await page.wait_for_selector('div[data-tt="components_PostTable_Container"]')
        video_list_locator = self.locator_base.locator('div[data-tt="components_PostTable_Container"] div[data-tt="components_PostInfoCell_Container"] a')
        if await video_list_locator.count():
            first_video_obj = await video_list_locator.nth(0).get_attribute('href')
            video_id = re.search(r'video/(\d+)', first_video_obj).group(1) if first_video_obj else None
            return video_id


    async def detect_upload_status(self, page):
        while True:
            try:
                # if await self.locator_base.locator('div.btn-post > button').get_attribute("disabled") is None:
                if await self.locator_base.locator(
                        'div.button-group > button >> text=Post').get_attribute("disabled") is None:
                    tiktok_logger.info("  [-]video uploaded.")
                    await self.ensure_modal_closed(page, wait_seconds=5)
                    break
                else:
                    tiktok_logger.info("  [-] video uploading...")
                    await asyncio.sleep(2)
                    if await self.locator_base.locator(
                            'button[aria-label="Select file"]').count():
                        tiktok_logger.info("  [-] found some error while uploading now retry...")
                        await self.handle_upload_error(page)
                    await self.ensure_modal_closed(page, wait_seconds=2)
            except:
                tiktok_logger.info("  [-] video uploading...")
                await asyncio.sleep(2)

    async def dismiss_auto_check_modal(self, page):
        handled = False
        try:
            dialog = page.get_by_role("dialog", name=re.compile("automatic content checks", re.I))
            if not await dialog.count():
                dialog = page.locator("div.common-modal").filter(has_text=re.compile("automatic content checks", re.I))
            if await dialog.count():
                cancel_btn = dialog.get_by_role("button", name=re.compile("cancel", re.I))
                if await cancel_btn.count():
                    await cancel_btn.click()
                    tiktok_logger.info("  [-] auto check modal closed via cancel button.")
                    await asyncio.sleep(0.5)
                    handled = True
                else:
                    close_btn = dialog.locator(".common-modal-close-icon")
                    if await close_btn.count():
                        await close_btn.click()
                        tiktok_logger.info("  [-] auto check modal closed via close icon.")
                        await asyncio.sleep(0.5)
                        handled = True
            if not handled:
                close_icon = page.locator("div.common-modal-close-icon").first
                if await close_icon.count():
                    await close_icon.click()
                    tiktok_logger.info("  [-] modal closed via global close icon.")
                    await asyncio.sleep(0.5)
                    handled = True
        except Exception as exc:
            tiktok_logger.warning(f"[+] dismiss auto check modal failed: {exc}")
        return handled

    async def ensure_modal_closed(self, page, wait_seconds=0):
        start_time = time.time()
        while True:
            handled = False
            if await self.dismiss_auto_check_modal(page):
                handled = True
            if await self.dismiss_continue_post_modal(page):
                handled = True
            if await self.dismiss_generic_cancelable_modal(page):
                handled = True
            if await self.wait_modal_overlay_hidden(page):
                handled = True
            if handled:
                await asyncio.sleep(0.3)
                continue
            if wait_seconds and (time.time() - start_time) < wait_seconds:
                await asyncio.sleep(0.5)
                continue
            break

    async def dismiss_generic_cancelable_modal(self, page):
        handled = False
        try:
            cancel_buttons = page.locator("div.common-modal button:has(.TUXButton-label:has-text('Cancel'))")
            while await cancel_buttons.count():
                await cancel_buttons.first.click()
                tiktok_logger.info("  [-] cancelable modal closed via cancel button.")
                await asyncio.sleep(0.5)
                handled = True
                cancel_buttons = page.locator("div.common-modal button:has(.TUXButton-label:has-text('Cancel'))")
        except Exception as exc:
            tiktok_logger.warning(f"[+] dismiss cancelable modal failed: {exc}")
        return handled

    async def dismiss_continue_post_modal(self, page):
        handled = False
        try:
            dialog = page.locator("div.common-modal").filter(has_text=re.compile("Continue to post", re.I))
            if not await dialog.count():
                dialog = page.get_by_role("dialog", name=re.compile("Continue to post", re.I))
            if await dialog.count():
                cancel_btn = dialog.locator("button:has(.TUXButton-label:has-text('Cancel'))")
                post_now_btn = dialog.locator("button:has(.TUXButton-label:has-text('Post now'))")
                if await cancel_btn.count():
                    await cancel_btn.click()
                    tiktok_logger.info("  [-] continue-post modal closed via cancel button.")
                    handled = True
                elif await post_now_btn.count():
                    await post_now_btn.click()
                    tiktok_logger.info("  [-] continue-post modal acknowledged via post now button.")
                    handled = True
                await asyncio.sleep(0.5)
        except Exception as exc:
            tiktok_logger.warning(f"[+] dismiss continue-post modal failed: {exc}")
        return handled

    async def wait_modal_overlay_hidden(self, page):
        try:
            overlay = page.locator("div.TUXModal-overlay[data-transition-status='open']")
            if await overlay.count():
                await overlay.wait_for(state='hidden', timeout=5000)
                return True
        except Exception as exc:
            tiktok_logger.warning(f"[+] wait overlay hidden failed: {exc}")
        return False

    async def save_debug_artifacts(self, page, base_name='debug_upload_page'):
        screenshot_path = f"{base_name}.png"
        html_path = f"{base_name}.html"
        try:
            await page.screenshot(path=screenshot_path, full_page=True)
            tiktok_logger.info(f"Screenshot saved to {screenshot_path}")
        except Exception as screenshot_error:
            tiktok_logger.warning(f"Failed to save screenshot: {screenshot_error}")
        try:
            html_content = await page.content()
            Path(html_path).write_text(html_content, encoding='utf-8')
            tiktok_logger.info(f"HTML snapshot saved to {html_path}")
        except Exception as html_error:
            tiktok_logger.warning(f"Failed to save HTML snapshot: {html_error}")

    async def wait_for_upload_surface(self, page):
        timeout_ms = 30000
        poll_interval = 0.5
        deadline = time.perf_counter() + timeout_ms / 1000
        candidate_locators = [
            ("upload iframe", page.locator('iframe[data-tt="Upload_index_iframe"]')),
            ("upload container", page.locator('div.upload-container')),
            ("new upload drag area", page.locator('[data-e2e="upload_drag_area"], [data-e2e="upload_card"]')),
            ("Select video text", page.locator('div:has-text("Select video to upload")')),
        ]
        button_locators = [
            ("Select video button", page.get_by_role("button", name=re.compile("select\\s+video", re.I))),
            ("Select file button", page.get_by_role("button", name=re.compile("select\\s+file", re.I))),
            ("Upload video button", page.get_by_role("button", name=re.compile("upload\\s+(video|files?)", re.I))),
        ]
        candidate_locators.extend(button_locators)

        logged_pending = set()
        last_error = None
        while time.perf_counter() < deadline:
            for description, locator in candidate_locators:
                try:
                    if await locator.first.is_visible():
                        tiktok_logger.info(f"{description} detected.")
                        return
                    if description not in logged_pending:
                        tiktok_logger.info(f"{description} not visible yet, waiting...")
                        logged_pending.add(description)
                except Exception as candidate_error:
                    last_error = candidate_error
            await asyncio.sleep(poll_interval)

        raise TimeoutError("Unable to detect any known upload containers/buttons.") from last_error

    async def choose_base_locator(self, page):
        # await page.wait_for_selector('div.upload-container')
        iframe_count = await page.locator('iframe[data-tt="Upload_index_iframe"]').count()
        tiktok_logger.info(f"Found {iframe_count} iframe(s)")

        # 调试：检查页面上是否有其他可能的选择器
        try:
            all_iframes = await page.locator('iframe').count()
            tiktok_logger.info(f"Total iframes on page: {all_iframes}")

            upload_container_count = await page.locator('div.upload-container').count()
            tiktok_logger.info(f"Found {upload_container_count} upload-container div(s)")

            # 检查是否有 "Select video" 相关的按钮
            select_video_buttons = await page.locator('button').filter(has_text="Select").count()
            tiktok_logger.info(f"Found {select_video_buttons} button(s) with 'Select' text")
        except Exception as debug_e:
            tiktok_logger.warning(f"Debug info collection failed: {debug_e}")

        if iframe_count > 0:
            self.locator_base = page.frame_locator(Tk_Locator.tk_iframe)
            tiktok_logger.info("Using iframe locator")
        else:
            self.locator_base = page.locator(Tk_Locator.default)
            tiktok_logger.info("Using default page locator") 

    async def main(self):
        async with async_playwright() as playwright:
            await self.upload(playwright)
