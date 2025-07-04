import os
import datetime
import yfinance as yf
import httpx
from openai import BaseModel
from config import BASE_URL,FMP_API_KEY,STOCK_NEWS_API_KEY
from mcp.types import TextContent
from mcp import McpError, ErrorData

def register_stock_market_tools(mcp):
    class RichToolDescription(BaseModel):
        description: str
        use_when: str
        side_effects: str | None
    
    GetStockPriceDesc = RichToolDescription(
        description="Get the current stock price for a given company with the symbol used in market. Use NSE symbols like RELIANCE.NS, TCS.NS, INFY.NS for Indian stocks. Add .NS for NSE stocks, .BO for BSE stocks.",
        use_when="user asks for stock price for a particular company, check if indian stcok then get symbola and add .NS",
        side_effects="Calls a stock market API"
    )
    @mcp.tool(description=GetStockPriceDesc.model_dump_json())
    async def get_stock_price(stock_symbol: str) -> TextContent:
        # try:
        #     url = f"https://financialmodelingprep.com/api/v3/quote/{stock_symbol}?apikey={FMP_API_KEY}"
        #     async with httpx.AsyncClient() as client:
        #         response = await client.get(url)
        #         data = response.json()
        #         if not data:
        #             return TextContent(type="text", text="📉 Could not find the stock symbol. Please check and try again.")

        #         stock = data[0]
        #         price = stock['price']
        #         change = stock['change']
        #         change_percent = stock['changesPercentage']
        #         name = stock['name']

        #         return TextContent(
        #             type="text",
        #             text=f"📈 {name} ({stock_symbol})\nPrice: ₹{price:.2f}\nChange: {change:+.2f} ({change_percent:+.2f}%)"
        #         )
        # except Exception as e:
        #     raise McpError(ErrorData(code=1, message=f"❌ Failed to fetch stock price: {e}"))        
        try:
            stock = yf.Ticker(stock_symbol.upper())
            data = stock.info

            price = data.get("regularMarketPrice")
            change = data.get("regularMarketChange")
            percent = data.get("regularMarketChangePercent")
            name = data.get("shortName", stock_symbol.upper())

            if price is None:
                raise McpError(ErrorData(code=404, message=f"No price data found for {stock_symbol.upper()}"))

            return TextContent(
                type="text",
                text=f"📈 {name} ({stock_symbol.upper()})\nPrice: ₹{price:.2f}\nChange: {change:+.2f} ({percent:+.2f}%)"
            )

        except McpError:
            raise
        except Exception as e:
            raise McpError(ErrorData(code=500, message=f"Yahoo Finance fetch failed: {e}"))
        

    CompareStocksToolDesc = RichToolDescription(
        description = "This tool returns a side-by-side comparison of the stock prices and percentage changes for up to 5 listed companies.",
        use_when = "user asks to compare stock prices of multiple companies",
        side_effects = "Calls a stock market API to fetch data for multiple companies based on the stock symbols provided."
    )
    @mcp.tool(description=CompareStocksToolDesc.model_dump_json())
    async def compare_stock_prices(stock_symbols: list[str]) -> TextContent:
        try:
            if not (1 <= len(stock_symbols) <= 5):
                raise McpError(ErrorData(code=400,message="Please provide 1 to 5 NSE symbols (e.g., RELIANCE.NS, INFY.NS)."))
            lines = []

            for symbol in stock_symbols:
                try:
                    stock = yf.Ticker(symbol.upper())
                    data = stock.info

                    price = data.get("regularMarketPrice")
                    change = data.get("regularMarketChange")
                    percent = data.get("regularMarketChangePercent")
                    name = data.get("shortName", symbol.upper())

                    if price is None:
                        lines.append(f"{symbol}: ❌ No data available.")
                        continue

                    lines.append(f"{name} ({symbol.upper()}): ₹{price:.2f} ({change:+.2f}, {percent:+.2f}%)")

                except Exception:
                    lines.append(f"{symbol.upper()}: ❌ Failed to retrieve data.")

            return TextContent(
                type="text",
                text="📊 NSE Stock Comparison:\n" + "\n".join(lines)
            )

        except McpError:
            raise
        except Exception as e:
            raise McpError(ErrorData(
                code=500,
                message=f"Unexpected error during stock comparison: {e}"
            ))


        #     symbol_string = ",".join(stock_symbols)
        #     url = f"https://financialmodelingprep.com/api/v3/quote/{symbol_string}?apikey={FMP_API_KEY}"
        #     async with httpx.AsyncClient() as client:
        #         response = await client.get(url)
        #         data = response.json()
        #         if not data:
        #             return TextContent(type="text", text="No stock data found for the provided symbols.")

        #         lines = []
        #         for stock in data:
        #             line = f"{stock['symbol']}: ₹{stock['price']:.2f} ({stock['changesPercentage']:+.2f}%)"
        #             lines.append(line)

        #         return TextContent(type="text", text="📊 Stock Comparison:\n" + "\n".join(lines))
        # except Exception as e:
        #     return TextContent(type="text", text=f"❌ Error during comparison: {e}")



    GetMarketNewsDesc = RichToolDescription(
        description="Get the latest market news.",
        use_when="user asks for latest market news",
        side_effects="Calls a market news API"
    )
    @mcp.tool(description=GetMarketNewsDesc.model_dump_json())
    async def get_market_news() -> TextContent:
        try:
            url = f"https://newsapi.org/v2/top-headlines?category=business&country=in&apiKey={STOCK_NEWS_API_KEY}"
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                data = response.json()
                if not data or not data.get('articles'):
                    return TextContent(type="text", text="📰 No news articles found.")

                articles = data['articles'][:5]  # Get top 5 articles
                news_items = [f"**{article['title']}**\n{article['description']}\n[Read more]({article['url']})" for article in articles]
                return TextContent(type="text", text="\n\n".join(news_items))
        except Exception as e:
            raise McpError(ErrorData(code=1, message=f"❌ Failed to fetch market news: {e}"))        
