'use client'

export default function DeepAuditLanding() {
  return (
    <div className="min-h-screen bg-white">
      {/* Hero Section */}
      <section className="border-b border-audit-gray-200">
        <div className="max-w-6xl mx-auto px-6 py-16">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            {/* Left: Title and Subtitle */}
            <div>
              <h1 className="text-4xl font-bold text-audit-gray-900 mb-4 leading-tight">
                Deep-Audit: Black-Box AI Safety & Governance Readiness Scan
              </h1>
              <p className="text-lg text-audit-gray-600 leading-relaxed">
                A non-invasive behavioral audit for production AI agents.
                No code access. No data extraction. No deployment required.
              </p>
            </div>

            {/* Right: Simple Flow Diagram */}
            <div className="bg-audit-gray-50 border border-audit-gray-200 p-8 rounded">
              <div className="font-mono text-sm text-audit-gray-700 space-y-3">
                <div className="flex items-center">
                  <span className="font-medium">Your AI API</span>
                  <span className="mx-4">→</span>
                  <span className="font-medium">Deep-Audit Scanner</span>
                </div>
                <div className="flex items-center pl-8">
                  <span className="mx-4">→</span>
                  <span className="font-medium">Risk Report (PDF)</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Trust & Scope Section - Three Columns */}
      <section className="border-b border-audit-gray-200">
        <div className="max-w-6xl mx-auto px-6 py-16">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {/* Column 1: Black-Box Only */}
            <div className="border border-audit-gray-200 p-6 rounded">
              <h3 className="text-lg font-semibold text-audit-gray-900 mb-3">
                Black-Box Only
              </h3>
              <ul className="space-y-2 text-audit-gray-600">
                <li>Tests behavior via your public API</li>
                <li>No access to source code or infrastructure</li>
              </ul>
            </div>

            {/* Column 2: Safe & Authorized */}
            <div className="border border-audit-gray-200 p-6 rounded">
              <h3 className="text-lg font-semibold text-audit-gray-900 mb-3">
                Safe & Authorized
              </h3>
              <ul className="space-y-2 text-audit-gray-600">
                <li>Rate-limited simulations</li>
                <li>Read-only prompts</li>
                <li>No state mutation</li>
                <li>Explicit authorization required</li>
              </ul>
            </div>

            {/* Column 3: Fast & Lightweight */}
            <div className="border border-audit-gray-200 p-6 rounded">
              <h3 className="text-lg font-semibold text-audit-gray-900 mb-3">
                Fast & Lightweight
              </h3>
              <ul className="space-y-2 text-audit-gray-600">
                <li>50–100 controlled behavioral scenarios</li>
                <li>Results in ~10 minutes</li>
                <li>No SDK, no onboarding</li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* What We Test */}
      <section className="border-b border-audit-gray-200">
        <div className="max-w-6xl mx-auto px-6 py-16">
          <h2 className="text-2xl font-bold text-audit-gray-900 mb-8">
            What We Test
          </h2>
          <div className="space-y-6">
            <div className="border-l-4 border-audit-gray-300 pl-4">
              <h3 className="text-lg font-semibold text-audit-gray-900 mb-2">
                Prompt Injection & Instruction Hijacking
              </h3>
              <p className="text-audit-gray-600">
                Evaluates whether the system can be manipulated to override its intended behavior through adversarial user inputs.
              </p>
            </div>

            <div className="border-l-4 border-audit-gray-300 pl-4">
              <h3 className="text-lg font-semibold text-audit-gray-900 mb-2">
                Hallucination & Fabrication
              </h3>
              <p className="text-audit-gray-600">
                Tests for generation of false information, non-existent features, or fabricated data not grounded in actual system capabilities.
              </p>
            </div>

            <div className="border-l-4 border-audit-gray-300 pl-4">
              <h3 className="text-lg font-semibold text-audit-gray-900 mb-2">
                PII / Policy / Secret Leakage
              </h3>
              <p className="text-audit-gray-600">
                Verifies the system does not disclose personal information, internal policies, or sensitive data without proper authorization.
              </p>
            </div>

            <div className="border-l-4 border-audit-gray-300 pl-4">
              <h3 className="text-lg font-semibold text-audit-gray-900 mb-2">
                Unsafe Action Compliance
              </h3>
              <p className="text-audit-gray-600">
                Assesses whether the system executes actions (refunds, deletions, modifications) without proper verification or authorization.
              </p>
            </div>

            <div className="border-l-4 border-audit-gray-300 pl-4">
              <h3 className="text-lg font-semibold text-audit-gray-900 mb-2">
                Encoding & Obfuscation Bypass
              </h3>
              <p className="text-audit-gray-600">
                Tests whether the system can be tricked via Base64, URL-encoding, leetspeak, or Unicode homoglyph payloads that disguise malicious instructions.
              </p>
            </div>

            <div className="border-l-4 border-audit-gray-300 pl-4">
              <h3 className="text-lg font-semibold text-audit-gray-900 mb-2">
                Multi-Language Injection
              </h3>
              <p className="text-audit-gray-600">
                Evaluates safety controls across Chinese, Japanese, Spanish, and mixed-language inputs to detect language-specific bypass vectors.
              </p>
            </div>

            <div className="border-l-4 border-audit-gray-300 pl-4">
              <h3 className="text-lg font-semibold text-audit-gray-900 mb-2">
                Indirect Prompt Injection
              </h3>
              <p className="text-audit-gray-600">
                Tests for hidden instructions embedded in document context, markdown payloads, fabricated error messages, and translation tasks.
              </p>
            </div>

            <div className="border-l-4 border-audit-gray-300 pl-4">
              <h3 className="text-lg font-semibold text-audit-gray-900 mb-2">
                Tool & Function Abuse
              </h3>
              <p className="text-audit-gray-600">
                Assesses whether the system can be manipulated into invoking dangerous tools, exporting bulk data, or executing unauthorized code.
              </p>
            </div>

            <div className="border-l-4 border-audit-gray-300 pl-4">
              <h3 className="text-lg font-semibold text-audit-gray-900 mb-2">
                Jailbreak & Persona Override
              </h3>
              <p className="text-audit-gray-600">
                Tests DAN-style persona overrides, fictional framing bypasses, academic research pretexts, and constraint boundary probing techniques.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="border-b border-audit-gray-200">
        <div className="max-w-6xl mx-auto px-6 py-16">
          <h2 className="text-2xl font-bold text-audit-gray-900 mb-8">
            How It Works
          </h2>
          <div className="space-y-6">
            <div className="flex items-start">
              <div className="flex-shrink-0 w-8 h-8 bg-audit-gray-900 text-white rounded flex items-center justify-center font-semibold mr-4">
                1
              </div>
              <p className="text-audit-gray-700 pt-1">
                You provide an API endpoint and test key
              </p>
            </div>

            <div className="flex items-start">
              <div className="flex-shrink-0 w-8 h-8 bg-audit-gray-900 text-white rounded flex items-center justify-center font-semibold mr-4">
                2
              </div>
              <p className="text-audit-gray-700 pt-1">
                Deep-Audit runs controlled behavioral simulations
              </p>
            </div>

            <div className="flex items-start">
              <div className="flex-shrink-0 w-8 h-8 bg-audit-gray-900 text-white rounded flex items-center justify-center font-semibold mr-4">
                3
              </div>
              <p className="text-audit-gray-700 pt-1">
                A structured risk report is generated
              </p>
            </div>

            <div className="flex items-start">
              <div className="flex-shrink-0 w-8 h-8 bg-audit-gray-900 text-white rounded flex items-center justify-center font-semibold mr-4">
                4
              </div>
              <p className="text-audit-gray-700 pt-1">
                You receive a PDF / Web report
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Output Preview - Static */}
      <section className="border-b border-audit-gray-200">
        <div className="max-w-6xl mx-auto px-6 py-16">
          <h2 className="text-2xl font-bold text-audit-gray-900 mb-8">
            Output Preview
          </h2>

          <div className="bg-audit-gray-50 border border-audit-gray-300 rounded p-8 max-w-2xl">
            <div className="mb-6">
              <div className="text-sm text-audit-gray-500 mb-2">Safety Score</div>
              <div className="text-3xl font-bold text-audit-red-600">
                42 / 100 (Critical)
              </div>
            </div>

            <div className="mb-6">
              <div className="text-sm text-audit-gray-500 mb-2">Risk Evidence</div>
              <div className="bg-audit-red-50 border border-audit-red-200 p-4 rounded">
                <p className="text-sm text-audit-gray-800 font-mono">
                  "The email on file is john.smith@example.com"
                </p>
              </div>
            </div>

            <div>
              <div className="text-sm text-audit-gray-500 mb-2">Taxonomy Breakdown</div>
              <div className="space-y-2">
                <div className="flex items-center">
                  <div className="w-32 text-sm text-audit-gray-700">Injection</div>
                  <div className="flex-1 bg-audit-gray-200 h-6 rounded overflow-hidden">
                    <div className="bg-audit-red-500 h-full" style={{width: '75%'}}></div>
                  </div>
                  <div className="w-12 text-right text-sm text-audit-gray-700">75%</div>
                </div>
                <div className="flex items-center">
                  <div className="w-32 text-sm text-audit-gray-700">Hallucination</div>
                  <div className="flex-1 bg-audit-gray-200 h-6 rounded overflow-hidden">
                    <div className="bg-audit-red-500 h-full" style={{width: '50%'}}></div>
                  </div>
                  <div className="w-12 text-right text-sm text-audit-gray-700">50%</div>
                </div>
                <div className="flex items-center">
                  <div className="w-32 text-sm text-audit-gray-700">Data Exposure</div>
                  <div className="flex-1 bg-audit-gray-200 h-6 rounded overflow-hidden">
                    <div className="bg-audit-red-500 h-full" style={{width: '100%'}}></div>
                  </div>
                  <div className="w-12 text-right text-sm text-audit-gray-700">100%</div>
                </div>
              </div>
            </div>

            <div className="mt-6 text-sm text-audit-gray-500 italic">
              Example report excerpt
            </div>
          </div>
        </div>
      </section>

      {/* Primary CTA */}
      <section className="border-b border-audit-gray-200">
        <div className="max-w-6xl mx-auto px-6 py-16 text-center">
          <a
            href="mailto:audit@safe-speed.com?subject=Request Free Audit Scan"
            className="inline-block bg-audit-gray-900 text-white px-8 py-3 rounded font-semibold hover:bg-audit-gray-800"
          >
            Request a Free Audit Scan
          </a>
          <p className="mt-4 text-sm text-audit-gray-500">
            Designed for evaluation. No data is stored beyond report generation.
          </p>
        </div>
      </section>

      {/* Footer - LEGAL & SCOPE DISCLAIMER */}
      <footer className="bg-audit-gray-50 border-t border-audit-gray-200">
        <div className="max-w-6xl mx-auto px-6 py-12">
          <div className="space-y-4 text-sm text-audit-gray-600">
            <p className="font-medium text-audit-gray-700">
              Authorization & Scope
            </p>
            <ul className="space-y-2 pl-4">
              <li>This audit was conducted with explicit authorization.</li>
              <li>No attempt was made to access infrastructure or bypass authentication.</li>
              <li>Deep-Audit performs application-layer behavioral analysis only.</li>
              <li>This assessment does not perform penetration testing.</li>
            </ul>
          </div>

          <div className="mt-8 pt-8 border-t border-audit-gray-200 text-center text-sm text-audit-gray-500">
            <p>Deep-Audit © 2025. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  )
}
