"""
高度なスクリーンショット管理機能
エラー時の自動撮影、比較、アノテーション機能を提供
"""

import os
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Tuple, Any
from playwright.sync_api import Page
from PIL import Image, ImageDraw, ImageFont
import json
import hashlib


class ScreenshotManager:
    """スクリーンショット管理クラス"""
    
    def __init__(self, base_dir: str = "tests/e2e/screenshots"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # カテゴリ別ディレクトリ
        self.categories = {
            "baseline": self.base_dir / "baseline",
            "actual": self.base_dir / "actual",
            "diff": self.base_dir / "diff",
            "error": self.base_dir / "error",
            "debug": self.base_dir / "debug"
        }
        
        for category_dir in self.categories.values():
            category_dir.mkdir(exist_ok=True)
    
    def capture(self, 
                page: Page,
                name: str,
                category: str = "actual",
                full_page: bool = True,
                clip: Optional[Dict[str, int]] = None,
                mask: Optional[List[str]] = None,
                highlight: Optional[List[str]] = None,
                annotations: Optional[List[Dict[str, Any]]] = None) -> Path:
        """高度なスクリーンショット撮影"""
        
        # ファイルパスの生成
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{name}_{timestamp}.png"
        filepath = self.categories.get(category, self.base_dir) / filename
        
        # マスク処理（動的要素を隠す）
        if mask:
            self._apply_masks(page, mask)
        
        # ハイライト処理
        if highlight:
            self._apply_highlights(page, highlight)
        
        # スクリーンショット撮影オプション
        screenshot_options = {
            "path": str(filepath),
            "full_page": full_page
        }
        
        if clip:
            screenshot_options["clip"] = clip
        
        # 撮影
        page.screenshot(**screenshot_options)
        
        # マスクとハイライトを解除
        if mask or highlight:
            self._remove_overlays(page)
        
        # アノテーション追加
        if annotations:
            self._add_annotations(filepath, annotations)
        
        # メタデータ保存
        self._save_metadata(filepath, {
            "name": name,
            "category": category,
            "timestamp": timestamp,
            "url": page.url,
            "viewport": page.viewport_size,
            "full_page": full_page,
            "clip": clip,
            "mask": mask,
            "highlight": highlight,
            "annotations": annotations
        })
        
        return filepath
    
    def capture_element(self,
                       page: Page,
                       selector: str,
                       name: str,
                       category: str = "actual",
                       padding: int = 0) -> Optional[Path]:
        """特定要素のスクリーンショット"""
        try:
            element = page.locator(selector).first
            if not element.is_visible():
                return None
            
            # 要素の位置とサイズを取得
            bbox = element.bounding_box()
            if not bbox:
                return None
            
            # パディングを追加
            clip = {
                "x": max(0, bbox["x"] - padding),
                "y": max(0, bbox["y"] - padding),
                "width": bbox["width"] + 2 * padding,
                "height": bbox["height"] + 2 * padding
            }
            
            return self.capture(
                page=page,
                name=f"{name}_element",
                category=category,
                full_page=False,
                clip=clip
            )
            
        except Exception as e:
            print(f"要素スクリーンショットエラー: {e}")
            return None
    
    def capture_series(self,
                      page: Page,
                      name: str,
                      actions: List[Dict[str, Any]],
                      category: str = "debug") -> List[Path]:
        """一連のアクションを実行しながらスクリーンショットを撮影"""
        screenshots = []
        
        for i, action in enumerate(actions):
            # アクション実行前のスクリーンショット
            before_path = self.capture(
                page=page,
                name=f"{name}_step{i}_before",
                category=category,
                annotations=[{
                    "text": f"Step {i}: {action.get('description', 'Action')}",
                    "position": (10, 10)
                }]
            )
            screenshots.append(before_path)
            
            # アクションを実行
            action_type = action.get("type")
            if action_type == "click":
                page.locator(action["selector"]).click()
            elif action_type == "fill":
                page.locator(action["selector"]).fill(action["value"])
            elif action_type == "wait":
                page.wait_for_timeout(action.get("timeout", 1000))
            elif action_type == "scroll":
                page.evaluate(f"window.scrollTo(0, {action.get('y', 0)})")
            
            # アクション実行後のスクリーンショット
            after_path = self.capture(
                page=page,
                name=f"{name}_step{i}_after",
                category=category
            )
            screenshots.append(after_path)
        
        return screenshots
    
    def capture_responsive(self,
                          page: Page,
                          name: str,
                          viewports: Optional[List[Dict[str, int]]] = None) -> Dict[str, Path]:
        """複数のビューポートでスクリーンショットを撮影"""
        if not viewports:
            viewports = [
                {"width": 1920, "height": 1080, "name": "desktop"},
                {"width": 1366, "height": 768, "name": "laptop"},
                {"width": 768, "height": 1024, "name": "tablet"},
                {"width": 375, "height": 812, "name": "mobile"}
            ]
        
        screenshots = {}
        original_viewport = page.viewport_size
        
        for viewport in viewports:
            # ビューポートを変更
            page.set_viewport_size({
                "width": viewport["width"],
                "height": viewport["height"]
            })
            
            # 少し待機（レイアウト調整のため）
            page.wait_for_timeout(500)
            
            # スクリーンショット撮影
            viewport_name = viewport.get("name", f"{viewport['width']}x{viewport['height']}")
            screenshot_path = self.capture(
                page=page,
                name=f"{name}_{viewport_name}",
                category="actual"
            )
            screenshots[viewport_name] = screenshot_path
        
        # 元のビューポートに戻す
        if original_viewport:
            page.set_viewport_size(original_viewport)
        
        return screenshots
    
    def compare(self,
                baseline_path: Path,
                actual_path: Path,
                threshold: float = 0.1) -> Tuple[bool, Optional[Path], float]:
        """スクリーンショットを比較"""
        try:
            from PIL import Image, ImageChops, ImageDraw
            import numpy as np
            
            # 画像を読み込み
            baseline = Image.open(baseline_path)
            actual = Image.open(actual_path)
            
            # サイズが異なる場合は不一致
            if baseline.size != actual.size:
                return False, None, 1.0
            
            # 差分を計算
            diff = ImageChops.difference(baseline, actual)
            
            # 差分を数値化
            diff_array = np.array(diff)
            diff_score = np.mean(diff_array) / 255.0
            
            # 閾値チェック
            is_match = diff_score <= threshold
            
            # 差分画像を生成
            if not is_match:
                diff_path = self.categories["diff"] / f"diff_{actual_path.name}"
                
                # 差分を強調表示
                diff_highlighted = Image.new('RGB', baseline.size)
                draw = ImageDraw.Draw(diff_highlighted)
                
                # ベースライン画像をグレースケールで表示
                baseline_gray = baseline.convert('L').convert('RGB')
                diff_highlighted.paste(baseline_gray)
                
                # 差分部分を赤で強調
                diff_mask = diff.convert('L')
                diff_colored = Image.new('RGB', baseline.size, (255, 0, 0))
                diff_highlighted.paste(diff_colored, mask=diff_mask)
                
                diff_highlighted.save(diff_path)
                
                return is_match, diff_path, diff_score
            
            return is_match, None, diff_score
            
        except Exception as e:
            print(f"画像比較エラー: {e}")
            return False, None, 1.0
    
    def _apply_masks(self, page: Page, selectors: List[str]):
        """要素をマスク（隠す）"""
        for selector in selectors:
            page.evaluate(f"""
                document.querySelectorAll('{selector}').forEach(el => {{
                    el.style.cssText += 'visibility: hidden !important;';
                    el.setAttribute('data-masked', 'true');
                }});
            """)
    
    def _apply_highlights(self, page: Page, selectors: List[str]):
        """要素をハイライト"""
        for selector in selectors:
            page.evaluate(f"""
                document.querySelectorAll('{selector}').forEach(el => {{
                    el.style.cssText += 'outline: 3px solid red !important; outline-offset: 2px !important;';
                    el.setAttribute('data-highlighted', 'true');
                }});
            """)
    
    def _remove_overlays(self, page: Page):
        """マスクとハイライトを解除"""
        page.evaluate("""
            // マスク解除
            document.querySelectorAll('[data-masked="true"]').forEach(el => {
                el.style.visibility = '';
                el.removeAttribute('data-masked');
            });
            
            // ハイライト解除
            document.querySelectorAll('[data-highlighted="true"]').forEach(el => {
                el.style.outline = '';
                el.style.outlineOffset = '';
                el.removeAttribute('data-highlighted');
            });
        """)
    
    def _add_annotations(self, image_path: Path, annotations: List[Dict[str, Any]]):
        """画像にアノテーションを追加"""
        try:
            img = Image.open(image_path)
            draw = ImageDraw.Draw(img)
            
            # フォントの設定（システムフォントを使用）
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 16)
            except:
                font = ImageFont.load_default()
            
            for annotation in annotations:
                text = annotation.get("text", "")
                position = annotation.get("position", (10, 10))
                color = annotation.get("color", "red")
                
                # テキストの背景
                bbox = draw.textbbox(position, text, font=font)
                padding = 5
                draw.rectangle(
                    [bbox[0] - padding, bbox[1] - padding, 
                     bbox[2] + padding, bbox[3] + padding],
                    fill="white",
                    outline=color
                )
                
                # テキスト
                draw.text(position, text, fill=color, font=font)
                
                # 矢印（オプション）
                if "arrow_to" in annotation:
                    arrow_end = annotation["arrow_to"]
                    draw.line([position[0], position[1] + 20, arrow_end[0], arrow_end[1]], 
                             fill=color, width=2)
                    # 矢印の先端
                    draw.polygon([
                        arrow_end,
                        (arrow_end[0] - 5, arrow_end[1] - 5),
                        (arrow_end[0] - 5, arrow_end[1] + 5)
                    ], fill=color)
            
            img.save(image_path)
            
        except Exception as e:
            print(f"アノテーション追加エラー: {e}")
    
    def _save_metadata(self, image_path: Path, metadata: Dict[str, Any]):
        """メタデータを保存"""
        metadata_path = image_path.with_suffix('.json')
        
        # 画像のハッシュを計算
        with open(image_path, 'rb') as f:
            metadata["hash"] = hashlib.md5(f.read()).hexdigest()
        
        # ファイルサイズ
        metadata["size"] = os.path.getsize(image_path)
        
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    def generate_gallery(self, category: str = "actual") -> Path:
        """スクリーンショットギャラリーHTMLを生成"""
        category_dir = self.categories.get(category, self.base_dir)
        screenshots = list(category_dir.glob("*.png"))
        
        html_content = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>Screenshot Gallery - {category}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background: #f5f5f5;
        }}
        .gallery {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
        }}
        .screenshot {{
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .screenshot img {{
            width: 100%;
            height: auto;
            display: block;
            cursor: pointer;
        }}
        .screenshot-info {{
            padding: 10px;
            font-size: 14px;
        }}
        .modal {{
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.9);
        }}
        .modal-content {{
            margin: 50px auto;
            display: block;
            max-width: 90%;
            max-height: 90%;
        }}
        .close {{
            position: absolute;
            top: 20px;
            right: 35px;
            color: #f1f1f1;
            font-size: 40px;
            font-weight: bold;
            cursor: pointer;
        }}
    </style>
</head>
<body>
    <h1>Screenshot Gallery - {category}</h1>
    <div class="gallery">
"""
        
        for screenshot in sorted(screenshots, reverse=True):
            # メタデータを読み込み
            metadata_path = screenshot.with_suffix('.json')
            metadata = {}
            if metadata_path.exists():
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
            
            html_content += f"""
        <div class="screenshot">
            <img src="{screenshot.name}" onclick="openModal(this.src)" alt="{screenshot.name}">
            <div class="screenshot-info">
                <strong>{screenshot.stem}</strong><br>
                <small>{metadata.get('timestamp', 'N/A')}</small><br>
                <small>{metadata.get('url', 'N/A')}</small>
            </div>
        </div>
"""
        
        html_content += """
    </div>
    
    <div id="modal" class="modal" onclick="closeModal()">
        <span class="close">&times;</span>
        <img class="modal-content" id="modalImg">
    </div>
    
    <script>
        function openModal(src) {
            document.getElementById('modal').style.display = 'block';
            document.getElementById('modalImg').src = src;
        }
        
        function closeModal() {
            document.getElementById('modal').style.display = 'none';
        }
    </script>
</body>
</html>
"""
        
        gallery_path = category_dir / "gallery.html"
        with open(gallery_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return gallery_path