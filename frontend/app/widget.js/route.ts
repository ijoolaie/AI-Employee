import { NextResponse } from "next/server";

export async function GET(request: Request) {
  const url = new URL(request.url);
  const key = url.searchParams.get("channel") || url.searchParams.get("public_key");
  if (!key) return new NextResponse("Missing channel", { status: 400 });
  const origin = url.origin;
  const script = `(function(){var f=document.createElement('iframe');f.src=${JSON.stringify(origin + "/chat/" + encodeURIComponent(key))};f.title='AI Sales Assistant';f.style='position:fixed;right:20px;bottom:20px;width:390px;height:680px;max-width:calc(100vw - 24px);max-height:calc(100vh - 24px);border:0;border-radius:16px;z-index:2147483647;box-shadow:0 18px 50px rgba(15,23,42,.22);background:white;';f.loading='lazy';document.body.appendChild(f);})();`;
  return new NextResponse(script, { headers: { "Content-Type": "application/javascript; charset=utf-8", "Cache-Control": "public, max-age=300" } });
}
