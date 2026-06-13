"""
智策报告PDF导出模块
"""

from datetime import datetime
import os
import tempfile
import asyncio
import io
from markdown_it import MarkdownIt
import yaml
from pdf_browser_launcher import get_browser_launch_options

# 条件导入pyppeteer，添加异常处理
try:
    from pyppeteer import launch
    has_pyppeteer = True
except (ImportError, OSError) as e:
    # 当pyppeteer无法导入时，使用reportlab作为备选
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    has_pyppeteer = False
    print(f"pyppeteer导入失败，将使用reportlab作为备选: {e}")


class SectorStrategyPDFGenerator:
    """智策报告PDF生成器"""
    
    def __init__(self):
        """初始化PDF生成器"""
        pass
    
    def _register_chinese_fonts(self):
        """注册中文字体 - 支持Windows和Linux系统"""
        try:
            # 检查是否已经注册过
            if 'ChineseFont' in pdfmetrics.getRegisteredFontNames():
                return 'ChineseFont'
            
            # Windows系统字体路径
            windows_font_paths = [
                'C:/Windows/Fonts/simsun.ttc',  # 宋体
                'C:/Windows/Fonts/simhei.ttf',  # 黑体
                'C:/Windows/Fonts/msyh.ttc',    # 微软雅黑
                'C:/Windows/Fonts/msyh.ttf',    # 微软雅黑（TTF格式）
            ]
            
            # Linux系统字体路径（Docker环境）
            linux_font_paths = [
                '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',  # 文泉驿正黑
                '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',  # 文泉驿微米黑
                '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',  # Noto Sans CJK
                '/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc',  # Noto Serif CJK
                '/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf',  # Droid字体
            ]
            
            # 合并所有可能的字体路径
            all_font_paths = windows_font_paths + linux_font_paths
            
            # 尝试注册字体
            for font_path in all_font_paths:
                if os.path.exists(font_path):
                    try:
                        pdfmetrics.registerFont(TTFont('ChineseFont', font_path))
                        print(f"✅ 成功注册中文字体: {font_path}")
                        return 'ChineseFont'
                    except Exception as e:
                        print(f"⚠️ 尝试注册字体 {font_path} 失败: {e}")
                        continue
            
            # 如果没有找到中文字体，打印警告并使用默认字体
            print("⚠️ 警告：未找到中文字体，PDF中文可能显示为方框")
            print("建议：在Docker中安装中文字体包")
            return 'Helvetica'
        except Exception as e:
            print(f"❌ 注册中文字体时出错: {e}")
            return 'Helvetica'
    
    def _get_chinese_font_css(self):
        """获取中文支持的CSS样式"""
        css_content = """
        @page {
            size: A4;
            margin: 2cm;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Microsoft YaHei', 'WenQuanYi Micro Hei', sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 100%;
            margin: 0 auto;
            padding: 0;
        }
        
        h1 {
            color: #667eea;
            text-align: center;
            font-size: 28px;
            margin-bottom: 20px;
            font-weight: bold;
        }
        
        h2 {
            color: #764ba2;
            border-left: 4px solid #667eea;
            padding-left: 15px;
            margin-top: 30px;
            margin-bottom: 15px;
            font-size: 20px;
        }
        
        h3 {
            color: #f093fb;
            margin-top: 20px;
            margin-bottom: 10px;
            font-size: 18px;
        }
        
        p {
            margin-bottom: 15px;
            text-align: justify;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        
        th {
            background-color: #667eea;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: bold;
        }
        
        td {
            padding: 10px;
            border: 1px solid #ddd;
        }
        
        tr:nth-child(even) {
            background-color: #f2f2f2;
        }
        
        hr {
            border: 0;
            height: 1px;
            background: #ccc;
            margin: 30px 0;
        }
        
        strong {
            font-weight: bold;
        }
        
        em {
            font-style: italic;
        }
        
        ul, ol {
            margin: 15px 0;
            padding-left: 30px;
        }
        
        li {
            margin-bottom: 8px;
        }
        
        .center {
            text-align: center;
        }
        
        .title-page {
            text-align: center;
            margin-top: 100px;
        }
        
        .subtitle {
            font-size: 20px;
            color: #666;
            margin-bottom: 50px;
        }
        
        .info-box {
            margin: 30px 0;
            padding: 20px;
            background-color: #f5f5f5;
            border-radius: 5px;
        }
        
        .disclaimer {
            margin: 50px 0 20px 0;
            font-style: italic;
            color: #666;
            text-align: center;
        }
        
        .small-text {
            font-size: 14px;
            color: #666;
        }
        """
        return css_content
    
    def _generate_markdown_content(self, data: dict) -> str:
        """生成Markdown格式的报告内容"""
        timestamp = data.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        final_predictions = data.get('final_predictions', {})
        agents_analysis = data.get('agents_analysis', {})
        comprehensive_report = data.get('comprehensive_report', '')
        
        # 生成Markdown内容
        markdown_content = f"""
# 智策板块策略分析报告

## AI驱动的多维度板块投资决策支持系统

---

<div class="center">
**生成时间:** {timestamp}<br/>
**分析周期:** 当日市场数据<br/>
**AI模型:** DeepSeek Multi-Agent System<br/>
**分析维度:** 宏观·板块·资金·情绪
</div>

<div class="disclaimer">
本报告由AI系统自动生成，仅供参考，不构成投资建议。
投资有风险，决策需谨慎。
</div>

---

## 一、市场概况

本报告基于{timestamp}的实时市场数据，
通过四位AI智能体的多维度分析，为您提供板块投资策略建议。

### 分析师团队
- **宏观策略师** - 分析宏观经济、政策导向、新闻事件
- **板块诊断师** - 分析板块走势、估值水平、轮动特征
- **资金流向分析师** - 分析主力资金、北向资金流向
- **市场情绪解码员** - 分析市场情绪、热度、赚钱效应

"""
        
        # 核心预测
        markdown_content += "\n---\n\n## 二、核心预测\n"
        
        if final_predictions.get('prediction_text'):
            # 文本格式预测
            markdown_content += f"\n{final_predictions['prediction_text']}\n"
        else:
            # JSON格式预测
            
            # 1. 板块多空
            long_short = final_predictions.get('long_short', {})
            bullish = long_short.get('bullish', [])
            bearish = long_short.get('bearish', [])
            
            if bullish or bearish:
                markdown_content += "\n### 2.1 板块多空预测\n\n"
                
                # 看多板块
                if bullish:
                    markdown_content += "**看多板块:**\n\n"
                    for idx, item in enumerate(bullish, 1):
                        markdown_content += f"{idx}. **{item.get('sector', 'N/A')}** (信心度: {item.get('confidence', 0)}/10)\n"
                        markdown_content += f"   理由: {item.get('reason', 'N/A')}\n"
                        markdown_content += f"   风险: {item.get('risk', 'N/A')}\n\n"
                
                # 看空板块
                if bearish:
                    markdown_content += "**看空板块:**\n\n"
                    for idx, item in enumerate(bearish, 1):
                        markdown_content += f"{idx}. **{item.get('sector', 'N/A')}** (信心度: {item.get('confidence', 0)}/10)\n"
                        markdown_content += f"   理由: {item.get('reason', 'N/A')}\n"
                        markdown_content += f"   风险: {item.get('risk', 'N/A')}\n\n"
            
            # 2. 板块轮动
            rotation = final_predictions.get('rotation', {})
            current_strong = rotation.get('current_strong', [])
            potential = rotation.get('potential', [])
            
            if current_strong or potential:
                markdown_content += "### 2.2 板块轮动预测\n\n"
                
                # 当前强势
                if current_strong:
                    markdown_content += "**当前强势板块:**\n\n"
                    for item in current_strong:
                        markdown_content += f"• **{item.get('sector', 'N/A')}**\n"
                        markdown_content += f"  轮动逻辑: {item.get('logic', 'N/A')[:100]}...\n"
                        markdown_content += f"  时间窗口: {item.get('time_window', 'N/A')}\n"
                        markdown_content += f"  操作建议: {item.get('advice', 'N/A')}\n\n"
                
                # 潜力接力
                if potential:
                    markdown_content += "**潜力接力板块:**\n\n"
                    for item in potential:
                        markdown_content += f"• **{item.get('sector', 'N/A')}**\n"
                        markdown_content += f"  轮动逻辑: {item.get('logic', 'N/A')[:100]}...\n"
                        markdown_content += f"  时间窗口: {item.get('time_window', 'N/A')}\n"
                        markdown_content += f"  操作建议: {item.get('advice', 'N/A')}\n\n"
            
            # 3. 板块热度
            heat = final_predictions.get('heat', {})
            hottest = heat.get('hottest', [])
            
            if hottest:
                markdown_content += "### 2.3 板块热度排行\n\n"
                markdown_content += "| 排名 | 板块 | 热度评分 | 趋势 | 持续性 |\n"
                markdown_content += "|------|------|----------|------|--------|\n"
                for idx, item in enumerate(hottest[:5], 1):
                    markdown_content += f"| {idx} | {item.get('sector', 'N/A')} | {item.get('score', 0)} | {item.get('trend', 'N/A')} | {item.get('sustainability', 'N/A')} |\n"
            
            # 4. 策略总结
            summary = final_predictions.get('summary', {})
            if summary:
                markdown_content += "### 2.4 策略总结\n\n"
                
                # 市场观点
                if summary.get('market_view'):
                    markdown_content += f"**市场观点:** {summary['market_view']}\n\n"
                
                # 核心机会
                if summary.get('key_opportunity'):
                    markdown_content += f"**核心机会:** {summary['key_opportunity']}\n\n"
                
                # 主要风险
                if summary.get('major_risk'):
                    markdown_content += f"**主要风险:** {summary['major_risk']}\n\n"
                
                # 整体策略
                if summary.get('strategy'):
                    markdown_content += f"**整体策略:** {summary['strategy']}\n\n"
        
        # AI智能体分析摘要
        if agents_analysis:
            markdown_content += "\n---\n\n## 三、AI智能体分析摘要\n\n"
            
            for key, agent_data in agents_analysis.items():
                agent_name = agent_data.get('agent_name', '未知分析师')
                agent_role = agent_data.get('agent_role', '')
                analysis = agent_data.get('analysis', '')
                
                # 分析师名称和职责
                markdown_content += f"### {agent_name}\n"
                if agent_role:
                    markdown_content += f"_{agent_role}_\n\n"
                
                # 分析内容（截取前500字）
                analysis_preview = analysis[:500] + "..." if len(analysis) > 500 else analysis
                markdown_content += f"{analysis_preview}\n\n"
        
        # 综合研判
        if comprehensive_report:
            markdown_content += "\n---\n\n## 四、综合研判\n\n"
            
            # 截取前1000字
            report_preview = comprehensive_report[:1000] + "..." if len(comprehensive_report) > 1000 else comprehensive_report
            markdown_content += f"{report_preview}\n\n"
        
        # 结束语
        markdown_content += "\n<div class='center'>\n<i>--- 报告结束 ---<br/>\n"
        markdown_content += "本报告由智策AI系统自动生成</i>\n</div>\n"
        
        return markdown_content
    
    async def _markdown_to_pdf_browser(self, markdown_content, output_path):
        """使用无头浏览器将Markdown转换为PDF"""
        # 将Markdown转换为HTML
        md = MarkdownIt()
        html_content = md.render(markdown_content)
        
        # 获取CSS样式
        css_content = self._get_chinese_font_css()
        
        # 完整的HTML结构
        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>智策板块策略分析报告</title>
            <style>
            {css_content}
            </style>
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """
        
        # 创建临时HTML文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as temp_html:
            temp_html.write(full_html)
            temp_html_path = temp_html.name
        
        try:
            # 启动浏览器，禁用信号处理以避免主线程限制
            launch_kwargs = get_browser_launch_options()
            browser = await launch(**launch_kwargs)

            # 创建新页面
            page = await browser.newPage()
            
            # 导航到临时HTML文件
            await page.goto(f'file://{temp_html_path}', waitUntil='networkidle0')
            
            # 生成PDF
            await page.pdf({
                'path': output_path,
                'format': 'A4',
                'margin': {
                    'top': '2cm',
                    'right': '2cm',
                    'bottom': '2cm',
                    'left': '2cm'
                },
                'printBackground': True
            })
            
            # 关闭浏览器
            await browser.close()
            
            print(f"使用浏览器生成PDF成功: {output_path}")
            return True
        except Exception as e:
            print(f"使用浏览器生成PDF失败: {e}")
            raise
        finally:
            # 清理临时文件
            if os.path.exists(temp_html_path):
                os.unlink(temp_html_path)
    
    def generate_pdf(self, result_data: dict, output_path: str = None) -> str:
        """
        生成智策分析PDF报告
        
        Args:
            result_data: 分析结果数据
            output_path: 输出路径，如果为None则生成临时文件
            
        Returns:
            PDF文件路径
        """
        try:
            # 如果没有指定输出路径，创建临时文件
            if output_path is None:
                temp_dir = tempfile.gettempdir()
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = os.path.join(temp_dir, f"智策报告_{timestamp}.pdf")
            
            # 1. 生成Markdown内容
            markdown_content = self._generate_markdown_content(result_data)
            
            if has_pyppeteer:
                # 使用浏览器生成PDF
                asyncio.run(self._markdown_to_pdf_browser(markdown_content, output_path))
            else:
                # reportlab备用方式生成PDF
                # 注册中文字体
                chinese_font = self._register_chinese_fonts()
                
                # 创建内存中的PDF文档
                buffer = io.BytesIO()
                doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
                
                # 获取样式
                styles = getSampleStyleSheet()
                
                # 创建自定义样式
                title_style = ParagraphStyle(
                    'CustomTitle',
                    parent=styles['Heading1'],
                    fontName=chinese_font,
                    fontSize=24,
                    spaceAfter=30,
                    alignment=TA_CENTER,
                    textColor=colors.darkblue
                )
                
                heading_style = ParagraphStyle(
                    'CustomHeading',
                    parent=styles['Heading2'],
                    fontName=chinese_font,
                    fontSize=16,
                    spaceAfter=12,
                    spaceBefore=20,
                    textColor=colors.darkblue
                )
                
                subheading_style = ParagraphStyle(
                    'CustomSubHeading',
                    parent=styles['Heading3'],
                    fontName=chinese_font,
                    fontSize=14,
                    spaceAfter=8,
                    spaceBefore=12,
                    textColor=colors.darkgreen
                )
                
                normal_style = ParagraphStyle(
                    'CustomNormal',
                    parent=styles['Normal'],
                    fontName=chinese_font,
                    fontSize=11,
                    spaceAfter=6,
                    alignment=TA_JUSTIFY
                )
                
                # 开始构建PDF内容
                story = []
                
                # 标题
                current_time = datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")
                story.append(Paragraph("智策板块策略分析报告", title_style))
                story.append(Paragraph(f"生成时间: {current_time}", normal_style))
                story.append(Spacer(1, 20))
                
                # 简单输出markdown内容，保留基本结构
                story.append(Paragraph("报告内容", heading_style))
                # 截取部分markdown内容显示
                preview_text = markdown_content[:1000] + "\n\n...(内容过长，仅显示部分)"
                story.append(Paragraph(preview_text.replace('\n', '<br/>'), normal_style))
                
                # 生成PDF
                doc.build(story)
                
                # 获取PDF内容并保存到文件
                pdf_content = buffer.getvalue()
                buffer.close()
                
                with open(output_path, 'wb') as f:
                    f.write(pdf_content)
            
            print(f"[PDF] 报告生成成功: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"[PDF] 生成失败: {e}")
            import traceback
            traceback.print_exc()
            raise


# 测试函数
if __name__ == "__main__":
    # 创建测试数据
    test_data = {
        "success": True,
        "timestamp": "2024-01-15 10:30:00",
        "final_predictions": {
            "long_short": {
                "bullish": [
                    {
                        "sector": "电子",
                        "confidence": 8,
                        "reason": "政策支持，资金持续流入",
                        "risk": "估值偏高，注意回调风险"
                    }
                ],
                "bearish": []
            },
            "rotation": {
                "current_strong": [],
                "potential": [],
                "declining": []
            },
            "heat": {
                "hottest": [
                    {"sector": "电子", "score": 95, "trend": "升温", "sustainability": "强"}
                ]
            },
            "summary": {
                "market_view": "市场整体向好",
                "key_opportunity": "科技板块",
                "major_risk": "估值风险",
                "strategy": "积极配置科技"
            }
        },
        "agents_analysis": {},
        "comprehensive_report": "综合研判内容..."
    }
    
    generator = SectorStrategyPDFGenerator()
    output_path = generator.generate_pdf(test_data)
    print(f"测试PDF生成: {output_path}")
