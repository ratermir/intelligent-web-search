from __future__ import annotations

from .fetch_complex import ComplexFetcher
from .fetch_simple import SimpleFetcher
from .heuristics import analyze
from .models import FetchMode, FetchResponse, InternalDecision, PublicStatus


class FetchOrchestrator:
    def __init__(self) -> None:
        self.simple = SimpleFetcher()
        self.complex = ComplexFetcher()

    async def startup(self) -> None:
        await self.complex.startup()

    async def shutdown(self) -> None:
        await self.complex.shutdown()

    async def fetch_content(self, url: str, prefer_complex: bool = False, debug: bool = False) -> FetchResponse:
        diagnostics: dict[str, object] = {}

        if prefer_complex:
            complex_result = await self.complex.fetch(url)
            return self._public_response(
                complex_result,
                status_override=None,
                reason_override=complex_result.error or "complex_fetch_requested",
                used_fallback=False,
                diagnostics=(self._debug_payload(diagnostics, complex_result, None) if debug else None),
            )

        simple_result = self.simple.fetch(url)
        decision = analyze(simple_result)
        diagnostics["simple_fetch"] = {
            "http_status": simple_result.http_status,
            "error": simple_result.error,
            "final_url": simple_result.final_url,
            "signals": decision.signals.model_dump(),
            "decision": decision.decision.value,
            "reason": decision.reason,
        }

        if decision.decision == InternalDecision.ACCEPT_SIMPLE:
            return self._public_response(
                simple_result,
                status_override=None,
                reason_override=decision.reason,
                used_fallback=False,
                diagnostics=diagnostics if debug else None,
            )

        if decision.decision == InternalDecision.TERMINAL_FAIL:
            return self._public_response(
                simple_result,
                status_override=PublicStatus.NOT_RETRIEVABLE,
                reason_override=decision.reason,
                used_fallback=False,
                diagnostics=diagnostics if debug else None,
            )

        complex_result = await self.complex.fetch(url)
        diagnostics["complex_fetch"] = {
            "http_status": complex_result.http_status,
            "error": complex_result.error,
            "final_url": complex_result.final_url,
        }

        if complex_result.ok and complex_result.text:
            return self._public_response(
                complex_result,
                status_override=PublicStatus.OK,
                reason_override="complex_fetch_succeeded_after_simple_rejected",
                used_fallback=True,
                diagnostics=diagnostics if debug else None,
            )

        reason = complex_result.error or "complex_fetch_failed_after_simple_rejected"
        return self._public_response(
            complex_result,
            status_override=PublicStatus.NOT_RETRIEVABLE,
            reason_override=reason,
            used_fallback=True,
            diagnostics=diagnostics if debug else None,
        )

    def _public_response(
        self,
        raw,
        status_override: PublicStatus | None,
        reason_override: str,
        used_fallback: bool,
        diagnostics: dict[str, object] | None,
    ) -> FetchResponse:
        if status_override is not None:
            status = status_override
        elif raw.ok and raw.text:
            status = PublicStatus.OK
        elif raw.text:
            status = PublicStatus.PARTIAL
        else:
            status = PublicStatus.NOT_RETRIEVABLE

        return FetchResponse(
            status=status,
            reason=reason_override,
            url=raw.url,
            final_url=raw.final_url,
            fetch_mode=raw.fetch_mode if raw.fetch_mode else FetchMode.NONE,
            used_fallback=used_fallback,
            title=raw.title,
            content=raw.text,
            markdown=raw.markdown,
            http_status=raw.http_status,
            diagnostics=diagnostics,
        )

    def _debug_payload(self, diagnostics, raw, decision):
        diagnostics["requested_complex_fetch"] = True
        diagnostics["complex_fetch"] = {
            "http_status": raw.http_status,
            "error": raw.error,
            "final_url": raw.final_url,
        }
        if decision is not None:
            diagnostics["decision"] = decision.model_dump()
        return diagnostics
