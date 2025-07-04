import os
import httpx
from openai import BaseModel
from mcp import McpError, ErrorData
from mcp.types import TextContent
from config import ATTESTER_API_KEY

def register_vehicle_tools(mcp):
    class RichToolDescription(BaseModel):
        description : str
        use_when : str
        side_effects :str | None
    
    ChallanStatusDesc = RichToolDescription(
        description="Check pending e‑challans (traffic fines) for a vehicle.",
        use_when="user wants to know if a vehicle has any pending challans",
        side_effects="Calls challan API and may expose vehicle info"
    )

    @mcp.tool(description=ChallanStatusDesc.model_dump_json())
    async def check_challan(vehicle_rc: str) -> list[TextContent]:
        url = f"https://api.emptra.com/emptra/vehicleChallanInfo"  # example endpoint
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, json={"vehicle_rc": vehicle_rc})
            data = resp.json()
            if not data.get("response"):
                return [TextContent(type="text", text="✅ No pending challans found.")]
            challans = data["response"]
            lines = [f"- Challan {c['id']}: ₹{c['amount']} for {c['violation']}" for c in challans]
            return [TextContent(type="text", text="🚨 Pending Challans:\n" + "\n".join(lines))]
        except Exception as e:
            raise McpError(ErrorData(code=500, message=f"Challan lookup failed: {e}"))


    # RCInfoDesc = RichToolDescription(
    #     description="Fetch vehicle registration details (RC info) from sandbox Cashfree API.",
    #     use_when="user asks for owner/model/RC status of a vehicle",
    #     side_effects="Calls Cashfree sandbox RC verification API"
    # )

    # @mcp.tool(description=RCInfoDesc.model_dump_json())
    # async def check_vehicle_rc(rc_number: str) -> list[TextContent]:
    #     api_url = "https://sandbox.cashfree.com/verification/vehicle-rc"
    #     client_id = CASHFREE_CLIENT_ID
    #     client_secret = CASHFREE_CLIENT_SECRET
    #     if not (client_id and client_secret):
    #         raise McpError(ErrorData(code=500, message="API credentials missing."))

    #     headers = {
    #         "Content-Type": "application/json",
    #         "x-client-id": client_id,
    #         "x-client-secret": client_secret
    #     }
    #     payload = {"verification_id": "req-" + rc_number, "vehicle_number": rc_number.upper()}

    #     try:
    #         async with httpx.AsyncClient() as client:
    #             resp = await client.post(api_url, headers=headers, json=payload, timeout=20)

    #         content = resp.text.strip()
    #         if not content:
    #             raise McpError(ErrorData(code=502, message="Empty response from RC API."))

    #         data = resp.json()
    #         print(f"RC API response: {data}")  # Debugging line
    #         if data.get("status") != "VALID":
    #             return [TextContent(type="text", text=f"❌ RC {rc_number} is invalid or not found.")]

    #         info = data
    #         text = (
    #             f"✅ RC Verified: {info.get('reg_no')}\n"
    #             f"- Owner: {info.get('owner')}\n"
    #             f"- Model: {info.get('vehicle_model')}\n"
    #             f"- Fuel: {info.get('type')}\n"
    #             f"- RC Expiry: {info.get('rc_expiry_date')}"
    #         )
    #         return [TextContent(type="text", text=text)]

    #     except httpx.RequestError as e:
    #         raise McpError(ErrorData(code=502, message=f"HTTP error contacting RC API: {e}"))
    #     except ValueError:
    #         raise McpError(ErrorData(code=502, message="RC API returned invalid JSON."))
    #     except Exception as e:
    #         raise McpError(ErrorData(code=500, message=f"RC lookup failed: {e}"))
    RCToolDesc = RichToolDescription(
        description="Fetch vehicle registration (RC) details from Parivahan database via Attestr.",
        use_when="user asks for RC info like owner, model, registration date",
        side_effects="Makes external API call to Attestr RC verification service"
    )

    @mcp.tool(description=RCToolDesc.model_dump_json())
    async def check_vehicle_rc(rc_number: str) -> list[TextContent]:
        """
        Input: Indian vehicle RC number, e.g. 'KA01AB1234'.
        
        Returns: Owner name, vehicle model, reg date, insurance, PUC, RTO circle, etc.
        """
        token = ATTESTER_API_KEY
        if not token:
            raise McpError(ErrorData(code=500, message="Attestr API token not configured."))

        url = "https://api.attestr.com/api/v2/public/checkx/rc"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Basic {token}"
        }
        payload = {"reg": rc_number.upper()}

        try:
            async with httpx.AsyncClient(timeout=20) as client:
                resp = await client.post(url, headers=headers, json=payload)

            # Check for non-JSON or empty response
            content = resp.text.strip()
            if not content:
                raise McpError(ErrorData(code=502, message="Empty response from Attestr RC API."))
            
            data = resp.json()
            valid = data.get("valid", False)
            message = data.get("message", "")

            if not valid:
                return [TextContent(type="text", text=f"❌ RC `{rc_number}` is invalid or not found: {message}")]

            # Extract fields
            fields = [
                ("Owner", data.get("owner")),
                ("Registration Date", data.get("registered")),
                ("Model", data.get("makerModel")),
                ("Fuel Type", data.get("fuelType")),
                ("RTO", data.get("rto")),
                ("PUC Expiry", data.get("pollutionCertificateUpto")),
                ("Insurance Upto", data.get("insuranceUpto")),
            ]
            details = "\n".join(f"- **{k}**: {v}" for k, v in fields if v)

            text = f"✅ **RC Details for {rc_number.upper()}**:\n" + details
            return [TextContent(type="text", text=text)]

        except httpx.RequestError as e:
            raise McpError(ErrorData(code=502, message=f"HTTP error: {e}"))
        except ValueError:
            raise McpError(ErrorData(code=502, message="Attestr RC API returned invalid JSON."))
        except Exception as e:
            raise McpError(ErrorData(code=500, message=f"RC lookup failed: {e}"))
