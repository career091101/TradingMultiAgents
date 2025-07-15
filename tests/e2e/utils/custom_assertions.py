"""
E2Eテスト用のカスタムアサーション
より詳細で有用なエラーメッセージを提供
"""

from typing import Any, Optional, Union, List, Dict, Callable
from playwright.sync_api import Page, Locator, expect
import re
import json
from datetime import datetime
import difflib


class CustomAssertions:
    """カスタムアサーションクラス"""
    
    def __init__(self, page: Page):
        self.page = page
        self.assertions_made = []
        self.failed_assertions = []
    
    def assert_element_visible(self, 
                              selector: str,
                              message: Optional[str] = None,
                              timeout: int = 5000) -> Locator:
        """要素が表示されていることを確認（詳細なエラーメッセージ付き）"""
        try:
            element = self.page.locator(selector)
            element.wait_for(state="visible", timeout=timeout)
            
            self._record_assertion("element_visible", True, {
                "selector": selector,
                "message": message
            })
            
            return element
            
        except Exception as e:
            # 詳細なエラー情報を収集
            error_details = self._collect_element_error_details(selector)
            
            custom_message = f"""
要素が表示されていません:
  セレクタ: {selector}
  タイムアウト: {timeout}ms
  URL: {self.page.url}
  
詳細情報:
{json.dumps(error_details, ensure_ascii=False, indent=2)}

推奨される対処法:
1. セレクタが正しいか確認してください
2. ページが完全に読み込まれているか確認してください
3. 要素が動的に生成される場合は、適切な待機処理を追加してください
"""
            
            if message:
                custom_message = f"{message}\n\n{custom_message}"
            
            self._record_assertion("element_visible", False, {
                "selector": selector,
                "message": message,
                "error": str(e),
                "details": error_details
            })
            
            raise AssertionError(custom_message) from e
    
    def assert_text_equals(self,
                          selector: str,
                          expected_text: str,
                          ignore_case: bool = False,
                          trim: bool = True,
                          message: Optional[str] = None):
        """テキストが一致することを確認（差分表示付き）"""
        try:
            element = self.page.locator(selector).first
            actual_text = element.text_content() or ""
            
            if trim:
                actual_text = actual_text.strip()
                expected_text = expected_text.strip()
            
            if ignore_case:
                matches = actual_text.lower() == expected_text.lower()
            else:
                matches = actual_text == expected_text
            
            if not matches:
                # 差分を生成
                diff = self._generate_text_diff(expected_text, actual_text)
                
                custom_message = f"""
テキストが一致しません:
  セレクタ: {selector}
  期待値: "{expected_text}"
  実際値: "{actual_text}"
  
差分:
{diff}

要素の状態:
  visible: {element.is_visible()}
  enabled: {element.is_enabled()}
"""
                
                if message:
                    custom_message = f"{message}\n\n{custom_message}"
                
                raise AssertionError(custom_message)
            
            self._record_assertion("text_equals", True, {
                "selector": selector,
                "expected": expected_text,
                "actual": actual_text
            })
            
        except Exception as e:
            self._record_assertion("text_equals", False, {
                "selector": selector,
                "expected": expected_text,
                "error": str(e)
            })
            raise
    
    def assert_text_contains(self,
                           selector: str,
                           substring: str,
                           ignore_case: bool = False,
                           message: Optional[str] = None):
        """テキストが部分文字列を含むことを確認"""
        element = self.page.locator(selector).first
        actual_text = element.text_content() or ""
        
        if ignore_case:
            contains = substring.lower() in actual_text.lower()
        else:
            contains = substring in actual_text
        
        if not contains:
            # 類似する部分を検索
            similar_parts = self._find_similar_text(actual_text, substring)
            
            custom_message = f"""
テキストに指定された文字列が含まれていません:
  セレクタ: {selector}
  探している文字列: "{substring}"
  実際のテキスト: "{actual_text[:200]}{'...' if len(actual_text) > 200 else ''}"
  
類似する部分:
{similar_parts}
"""
            
            if message:
                custom_message = f"{message}\n\n{custom_message}"
            
            raise AssertionError(custom_message)
    
    def assert_element_count(self,
                           selector: str,
                           expected_count: int,
                           operator: str = "equals",
                           message: Optional[str] = None):
        """要素数を確認"""
        elements = self.page.locator(selector).all()
        actual_count = len(elements)
        
        operators = {
            "equals": lambda a, e: a == e,
            "greater": lambda a, e: a > e,
            "greater_equal": lambda a, e: a >= e,
            "less": lambda a, e: a < e,
            "less_equal": lambda a, e: a <= e,
            "not_equals": lambda a, e: a != e
        }
        
        if operator not in operators:
            raise ValueError(f"不明な演算子: {operator}")
        
        if not operators[operator](actual_count, expected_count):
            # 見つかった要素の詳細
            element_details = []
            for i, elem in enumerate(elements[:5]):  # 最初の5個まで
                try:
                    element_details.append({
                        "index": i,
                        "text": elem.text_content()[:50],
                        "visible": elem.is_visible()
                    })
                except:
                    element_details.append({"index": i, "error": "要素情報取得エラー"})
            
            custom_message = f"""
要素数が期待値と一致しません:
  セレクタ: {selector}
  期待値: {expected_count} ({operator})
  実際値: {actual_count}
  
見つかった要素:
{json.dumps(element_details, ensure_ascii=False, indent=2)}
"""
            
            if message:
                custom_message = f"{message}\n\n{custom_message}"
            
            raise AssertionError(custom_message)
    
    def assert_url_matches(self,
                         pattern: Union[str, re.Pattern],
                         message: Optional[str] = None):
        """URLがパターンに一致することを確認"""
        current_url = self.page.url
        
        if isinstance(pattern, str):
            if not re.search(pattern, current_url):
                custom_message = f"""
URLがパターンに一致しません:
  現在のURL: {current_url}
  期待パターン: {pattern}
  
ナビゲーション履歴:
{self._get_navigation_history()}
"""
                
                if message:
                    custom_message = f"{message}\n\n{custom_message}"
                
                raise AssertionError(custom_message)
        else:
            if not pattern.match(current_url):
                raise AssertionError(f"URL '{current_url}' がパターン '{pattern.pattern}' に一致しません")
    
    def assert_element_state(self,
                           selector: str,
                           state: Dict[str, Any],
                           message: Optional[str] = None):
        """要素の状態を複合的に確認"""
        element = self.page.locator(selector).first
        
        state_checks = {
            "visible": element.is_visible,
            "enabled": element.is_enabled,
            "checked": element.is_checked,
            "editable": element.is_editable,
            "empty": lambda: not element.text_content(),
            "focused": lambda: element.evaluate("el => document.activeElement === el")
        }
        
        failed_checks = []
        actual_state = {}
        
        for state_name, expected_value in state.items():
            if state_name in state_checks:
                actual_value = state_checks[state_name]()
                actual_state[state_name] = actual_value
                
                if actual_value != expected_value:
                    failed_checks.append(f"{state_name}: 期待値={expected_value}, 実際値={actual_value}")
        
        if failed_checks:
            custom_message = f"""
要素の状態が期待値と一致しません:
  セレクタ: {selector}
  
失敗したチェック:
{chr(10).join(f"  - {check}" for check in failed_checks)}

実際の状態:
{json.dumps(actual_state, ensure_ascii=False, indent=2)}

要素の詳細:
  タグ名: {element.evaluate('el => el.tagName')}
  クラス: {element.get_attribute('class')}
  ID: {element.get_attribute('id')}
"""
            
            if message:
                custom_message = f"{message}\n\n{custom_message}"
            
            raise AssertionError(custom_message)
    
    def assert_api_response(self,
                          response_promise,
                          expected_status: Optional[int] = None,
                          expected_body: Optional[Dict] = None,
                          message: Optional[str] = None):
        """API レスポンスを確認"""
        response = response_promise.value
        
        errors = []
        
        # ステータスコードチェック
        if expected_status and response.status != expected_status:
            errors.append(f"ステータスコード: 期待値={expected_status}, 実際値={response.status}")
        
        # レスポンスボディチェック
        if expected_body:
            try:
                actual_body = response.json()
                body_diff = self._compare_json(expected_body, actual_body)
                if body_diff:
                    errors.append(f"レスポンスボディ:\n{body_diff}")
            except Exception as e:
                errors.append(f"JSONパースエラー: {e}")
        
        if errors:
            custom_message = f"""
APIレスポンスが期待値と一致しません:
  URL: {response.url}
  メソッド: {response.request.method}
  
エラー:
{chr(10).join(f"  - {error}" for error in errors)}

レスポンスヘッダー:
{json.dumps(dict(response.headers), ensure_ascii=False, indent=2)}
"""
            
            if message:
                custom_message = f"{message}\n\n{custom_message}"
            
            raise AssertionError(custom_message)
    
    def assert_no_console_errors(self,
                               ignore_patterns: Optional[List[str]] = None,
                               message: Optional[str] = None):
        """コンソールエラーがないことを確認"""
        console_messages = []
        
        def handle_console_message(msg):
            if msg.type in ["error", "warning"]:
                text = msg.text
                
                # 無視パターンチェック
                if ignore_patterns:
                    for pattern in ignore_patterns:
                        if re.search(pattern, text, re.IGNORECASE):
                            return
                
                console_messages.append({
                    "type": msg.type,
                    "text": text,
                    "location": msg.location
                })
        
        self.page.on("console", handle_console_message)
        
        # 少し待機してメッセージを収集
        self.page.wait_for_timeout(1000)
        
        if console_messages:
            custom_message = f"""
コンソールにエラーまたは警告が出力されました:
  URL: {self.page.url}
  
メッセージ:
{json.dumps(console_messages, ensure_ascii=False, indent=2)}

対処法:
1. 開発者ツールのコンソールで詳細を確認してください
2. JavaScriptエラーの原因を特定して修正してください
3. 必要に応じて ignore_patterns にパターンを追加してください
"""
            
            if message:
                custom_message = f"{message}\n\n{custom_message}"
            
            raise AssertionError(custom_message)
    
    def assert_accessibility(self,
                           selector: Optional[str] = None,
                           rules: Optional[List[str]] = None,
                           message: Optional[str] = None):
        """アクセシビリティチェック"""
        # axe-coreを注入して実行
        self.page.add_script_tag(url="https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.4.1/axe.min.js")
        
        # アクセシビリティテストを実行
        if selector:
            results = self.page.evaluate(f"axe.run(document.querySelector('{selector}'))")
        else:
            results = self.page.evaluate("axe.run()")
        
        violations = results.get("violations", [])
        
        if rules:
            violations = [v for v in violations if v["id"] in rules]
        
        if violations:
            violation_summary = []
            for violation in violations:
                violation_summary.append({
                    "id": violation["id"],
                    "impact": violation["impact"],
                    "description": violation["description"],
                    "nodes": len(violation["nodes"])
                })
            
            custom_message = f"""
アクセシビリティ違反が検出されました:
  URL: {self.page.url}
  違反数: {len(violations)}
  
違反内容:
{json.dumps(violation_summary, ensure_ascii=False, indent=2)}

修正方法:
1. 各違反の詳細を確認してください
2. WCAG 2.1 ガイドラインに従って修正してください
3. aria-label や role 属性を適切に設定してください
"""
            
            if message:
                custom_message = f"{message}\n\n{custom_message}"
            
            raise AssertionError(custom_message)
    
    def _collect_element_error_details(self, selector: str) -> Dict[str, Any]:
        """要素に関する詳細なエラー情報を収集"""
        details = {
            "selector": selector,
            "found_elements": 0,
            "similar_elements": [],
            "parent_visible": False,
            "dom_state": "unknown"
        }
        
        try:
            # 要素数を確認
            elements = self.page.locator(selector).all()
            details["found_elements"] = len(elements)
            
            # 類似する要素を検索
            if "data-testid" in selector:
                testid = re.search(r'data-testid="([^"]+)"', selector)
                if testid:
                    similar = self.page.locator(f'[data-testid*="{testid.group(1)[:5]}"]').all()
                    details["similar_elements"] = [elem.get_attribute("data-testid") for elem in similar[:5]]
            
            # DOM状態を確認
            details["dom_state"] = self.page.evaluate("document.readyState")
            
        except:
            pass
        
        return details
    
    def _generate_text_diff(self, expected: str, actual: str) -> str:
        """テキストの差分を生成"""
        diff = difflib.unified_diff(
            expected.splitlines(keepends=True),
            actual.splitlines(keepends=True),
            fromfile="期待値",
            tofile="実際値",
            n=3
        )
        return ''.join(diff)
    
    def _find_similar_text(self, text: str, substring: str) -> str:
        """類似するテキストを検索"""
        # 簡易的な類似度チェック
        words = text.split()
        similar_words = []
        
        for word in words:
            similarity = difflib.SequenceMatcher(None, substring.lower(), word.lower()).ratio()
            if similarity > 0.6:
                similar_words.append(f"{word} (類似度: {similarity:.2f})")
        
        if similar_words:
            return "\n".join(similar_words[:5])
        else:
            return "類似する文字列が見つかりませんでした"
    
    def _compare_json(self, expected: Dict, actual: Dict) -> Optional[str]:
        """JSONオブジェクトを比較"""
        import deepdiff
        
        diff = deepdiff.DeepDiff(expected, actual, ignore_order=True)
        
        if diff:
            return json.dumps(diff, ensure_ascii=False, indent=2)
        
        return None
    
    def _get_navigation_history(self) -> str:
        """ナビゲーション履歴を取得"""
        try:
            history = self.page.evaluate("""
                () => {
                    const entries = performance.getEntriesByType('navigation');
                    return entries.map(e => ({
                        name: e.name,
                        type: e.type,
                        duration: e.duration
                    }));
                }
            """)
            return json.dumps(history, ensure_ascii=False, indent=2)
        except:
            return "履歴取得エラー"
    
    def _record_assertion(self, assertion_type: str, passed: bool, details: Dict[str, Any]):
        """アサーションを記録"""
        record = {
            "type": assertion_type,
            "passed": passed,
            "timestamp": datetime.now().isoformat(),
            "details": details
        }
        
        self.assertions_made.append(record)
        
        if not passed:
            self.failed_assertions.append(record)
    
    def get_assertion_summary(self) -> Dict[str, Any]:
        """アサーションのサマリーを取得"""
        return {
            "total": len(self.assertions_made),
            "passed": sum(1 for a in self.assertions_made if a["passed"]),
            "failed": len(self.failed_assertions),
            "assertions": self.assertions_made
        }


# 便利な関数形式のアサーション
def assert_element_visible(page: Page, selector: str, **kwargs):
    """要素が表示されていることを確認"""
    assertions = CustomAssertions(page)
    return assertions.assert_element_visible(selector, **kwargs)


def assert_text_equals(page: Page, selector: str, expected_text: str, **kwargs):
    """テキストが一致することを確認"""
    assertions = CustomAssertions(page)
    return assertions.assert_text_equals(selector, expected_text, **kwargs)


def assert_no_console_errors(page: Page, **kwargs):
    """コンソールエラーがないことを確認"""
    assertions = CustomAssertions(page)
    return assertions.assert_no_console_errors(**kwargs)