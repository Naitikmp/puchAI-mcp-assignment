# ascii_art_generator.py

import re
from typing import List, Dict, Optional
from pyfiglet import Figlet
from mcp import McpError, ErrorData
from mcp.types import TextContent
from pydantic import BaseModel

class AsciiArtGenerator:
    def __init__(self):
        # Popular fonts that work well for messaging
        self.popular_fonts = {
            'default': 'standard',
            'big': 'big',
            'block': 'block',
            'bubble': 'bubble',
            'digital': 'digital',
            'doom': 'doom',
            'epic': 'epic',
            'gothic': 'gothic',
            'graffiti': 'graffiti',
            'shadow': 'shadow',
            'slant': 'slant',
            'small': 'small',
            'thick': 'thick',
            'thin': 'thin'
        }
        
        # Decorative elements
        self.decorations = {
            'stars': '✨⭐🌟💫⭐✨',
            'hearts': '💖💕💗💓💝💖',
            'fire': '🔥🔥🔥🔥🔥🔥',
            'party': '🎉🎊🎈🎁🎉🎊',
            'crown': '👑👑👑👑👑👑',
            'rocket': '🚀🚀🚀🚀🚀🚀',
            'flowers': '🌸🌺🌻🌹🌷🌸',
            'music': '🎵🎶🎵🎶🎵🎶'
        }
        
        # Message type templates
        self.message_templates = {
            'birthday': {
                'decoration': 'party',
                'prefix': '🎂 HAPPY BIRTHDAY 🎂',
                'suffix': '🎉 Have an amazing day! 🎉'
            },
            'congratulations': {
                'decoration': 'crown',
                'prefix': '🏆 CONGRATULATIONS 🏆',
                'suffix': '🌟 Well deserved! 🌟'
            },
            'celebration': {
                'decoration': 'fire',
                'prefix': '🎊 CELEBRATION TIME 🎊',
                'suffix': '🎉 Let\'s celebrate! 🎉'
            },
            'love': {
                'decoration': 'hearts',
                'prefix': '💕 WITH LOVE 💕',
                'suffix': '💖 Always in my heart 💖'
            },
            'success': {
                'decoration': 'rocket',
                'prefix': '🚀 SUCCESS 🚀',
                'suffix': '⭐ You did it! ⭐'
            }
        }
    
    def generate_ascii_art(self, text: str, style: str = 'default', 
                          decoration: str = None, message_type: str = None) -> str:
        """Generate ASCII art with optional decorations and message types"""
        try:
            # Clean and validate input
            text = text.strip()
            if not text:
                return "❌ Please provide text to convert"
            
            # Limit text length for better display
            if len(text) > 20:
                text = text[:20]
            
            # Get font (default to 'standard' if not found)
            font = self.popular_fonts.get(style, 'standard')
            
            # Generate ASCII art
            figlet = Figlet(font=font, width=70)
            ascii_art = figlet.renderText(text).rstrip()
            
            # Apply message type template if specified
            print("Outisde here")
            if style and style in self.message_templates:
                print("Inside here")
                template = self.message_templates[style]
                print("Below here here")
                decoration = template['decoration']
                
                # Build complete message
                message_parts = []
                
                # Add prefix
                message_parts.append(template['prefix'])
                message_parts.append("")
                
                # Add decoration header
                if decoration in self.decorations:
                    message_parts.append(self.decorations[decoration])
                    message_parts.append("")
                
                # Add ASCII art in code block
                message_parts.append("```")
                message_parts.append(ascii_art)
                message_parts.append("```")
                
                # Add decoration footer
                if decoration in self.decorations:
                    message_parts.append("")
                    message_parts.append(self.decorations[decoration])
                
                # Add suffix
                message_parts.append("")
                message_parts.append(template['suffix'])
                
                print('\n'.join(message_parts))
                return '\n'.join(message_parts)
            
            # Regular ASCII art with optional decoration
            else:
                message_parts = []
                
                # Add decoration header
                if decoration and decoration in self.decorations:
                    message_parts.append(self.decorations[decoration])
                    message_parts.append("")
                
                # Add ASCII art in code block for better WhatsApp formatting
                message_parts.append("```")
                message_parts.append(ascii_art)
                message_parts.append("```")
                
                # Add decoration footer
                if decoration and decoration in self.decorations:
                    message_parts.append("")
                    message_parts.append(self.decorations[decoration])
                
                return '\n'.join(message_parts)
            
        except Exception as e:
            # Fallback to simple text if ASCII generation fails
            return f"❌ Could not generate ASCII art: {str(e)}"
    
    def get_available_options(self) -> str:
        """Get list of available styles and options"""
        output = "🎨 **ASCII Art Generator Options**\n\n"
        
        output += "🎭 **Available Styles:**\n"
        for style, font in self.popular_fonts.items():
            output += f"• `{style}` - {font} font\n"
        
        output += "\n✨ **Decorations:**\n"
        for decoration, emojis in self.decorations.items():
            output += f"• `{decoration}` - {emojis}\n"
        
        output += "\n🎯 **Message Types:**\n"
        for msg_type, template in self.message_templates.items():
            output += f"• `{msg_type}` - {template['prefix']}\n"
        
        output += "\n💡 **Usage Examples:**\n"
        output += "• `generate_ascii_art('HELLO')` - Basic ASCII art\n"
        output += "• `generate_ascii_art('PARTY', 'big', 'fire')` - With style and decoration\n"
        output += "• `generate_ascii_art('Sarah', message_type='birthday')` - Birthday message\n"
        
        return output

def register_ascii_art_tools(mcp):
    """Register ASCII art tool with MCP"""
    generator = AsciiArtGenerator()
    
    class RichToolDescription(BaseModel):
        description: str
        use_when: str
        side_effects: str | None

    # Single comprehensive ASCII art tool
    AsciiArtToolDesc = RichToolDescription(
        description="Generate ASCII art from text with customizable styles, decorations, and message types. Perfect for WhatsApp messages, social media, and celebrations.",
        use_when="user wants to create ASCII art, decorative text, stylized messages, birthday wishes, congratulations, or any special formatted text",
        side_effects="Creates ASCII art text ready for copying and sharing"
    )

    @mcp.tool(description=AsciiArtToolDesc.model_dump_json())
    async def generate_ascii_art(
        text: str, 
        style: str = 'default',
        decoration: str = None,
        message_type: str = None
    ) -> list[TextContent]:
        """Generate ASCII art with optional styling and decorations
        
        Args:
            text: The text to convert to ASCII art
            style: Font style (default, big, block, bubble, digital, doom, epic, gothic, graffiti, shadow, slant, small, thick, thin)
            decoration: Add emoji decorations (stars, hearts, fire, party, crown, rocket, flowers, music)
            message_type: Pre-built message templates (birthday, congratulations, celebration, love, success)
        """
        try:
            if not text or not text.strip():
                # Show available options if no text provided
                options = generator.get_available_options()
                return [TextContent(type="text", text=options)]
            
            # Generate the ASCII art
            result = generator.generate_ascii_art(text, style, decoration, message_type)
            
            # Create the response
            output = f"🎨 **ASCII Art Generated**\n\n"
            output += f"📝 **Text:** {text}\n"
            output += f"🎭 **Style:** {style}\n"
            
            if decoration:
                output += f"✨ **Decoration:** {decoration}\n"
            if message_type:
                output += f"🎯 **Message Type:** {message_type}\n"
            
            output += f"\n**📋 Your ASCII Art:**\n\n{result}\n\n"
            
            # Add usage tips
            output += "💡 **Tips:**\n"
            output += "• Copy the entire message above\n"
            output += "• Paste directly into WhatsApp, Telegram, or any messaging app\n"
            output += "• The ``` marks create code blocks for better formatting\n"
            output += "• Try different styles and decorations for variety!\n\n"
            
            # Show quick options
            output += "🔧 **Quick Options:**\n"
            output += "• Use `style='big'` for large text\n"
            output += "• Use `decoration='fire'` for fire emojis\n"
            output += "• Use `message_type='birthday'` for birthday messages\n"
            output += "• Leave parameters empty for simple ASCII art"
            
            return [TextContent(type="text", text=output)]
            
        except Exception as e:
            error_msg = f"❌ **ASCII Art Generation Failed**\n\n"
            error_msg += f"**Error:** {str(e)}\n\n"
            error_msg += "**Try:**\n"
            error_msg += "• Using shorter text (under 20 characters)\n"
            error_msg += "• Using a different style\n"
            error_msg += "• Checking spelling of style/decoration names\n\n"
            error_msg += generator.get_available_options()
            
            return [TextContent(type="text", text=error_msg)]