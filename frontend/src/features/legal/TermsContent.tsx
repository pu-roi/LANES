import { LegalSection } from "./LegalSection";

export function TermsContent() {
  return (
    <div className="space-y-7 text-sm leading-6 text-slate-700 sm:text-base sm:leading-7">
      <LegalSection id="service" title="1. The service">
        <p>
          LANES provides flood reports, public alerts, community features, maps, and suggested routes for
          information and planning. Conditions can change quickly. A report may be incomplete, delayed,
          estimated, or awaiting review. A route shown on the map is not a guarantee that a road is open or safe.
        </p>
        <p>
          Follow road signs, official advisories, and directions from emergency authorities. Do not use LANES
          as a substitute for emergency services, on scene judgment, or official evacuation instructions.
        </p>
      </LegalSection>

      <LegalSection id="accounts" title="2. Accounts and access">
        <p>
          Provide accurate information when registering and keep your login details secure. You are responsible
          for activity carried out through your account. Tell us promptly if you suspect unauthorized access.
          Some features require a verified account and may be limited by role or moderation status.
        </p>
      </LegalSection>

      <LegalSection id="contributions" title="3. Reports and community contributions">
        <p>
          Submit reports in good faith and describe what you actually observed or can support. Do not post
          false flood claims, threats, harassment, spam, unlawful material, or another person&apos;s private
          information without a lawful reason. Avoid images that reveal people or private details unnecessarily.
        </p>
        <p>
          You keep ownership of content you submit. By submitting it, you permit LANES to store, review,
          reproduce, and display it as needed to operate the requested features, publish approved public
          content, and investigate corrections or abuse. This permission ends when the content is removed,
          subject to records that must be kept for a legitimate moderation, dispute, or legal purpose.
          We may reject, label, hide, or remove content that is inaccurate, unsafe, or violates these terms.
        </p>
      </LegalSection>

      <LegalSection id="sources" title="4. Sources and third party services">
        <p>
          LANES may show information from news sources, public datasets, map providers, routing services,
          and community contributors. We identify estimated flood zones and source based alerts where
          applicable; they are not field verification. Third party content and services can change or become
          unavailable. Follow their applicable terms when using their services directly.
        </p>
      </LegalSection>

      <LegalSection id="availability" title="5. Availability and responsibility">
        <p>
          We may update or temporarily suspend features for maintenance, safety, or abuse prevention.
          We work to correct errors, but cannot promise uninterrupted service, complete coverage, or
          real time accuracy. To the extent permitted by Philippine law, LANES is provided without a
          guarantee of a particular route or safety outcome. Nothing here limits rights or liabilities
          that the law does not allow us to exclude.
        </p>
      </LegalSection>

      <LegalSection id="privacy" title="6. Privacy">
        <p>
          Our Privacy Policy explains
          how account, location, contribution, and usage data are handled and how to make a data rights request.
          Public submissions can be seen by others, so review them before posting.
        </p>
      </LegalSection>

      <LegalSection id="changes-and-contact" title="7. Changes and contact">
        <p>
          We may revise these terms as LANES develops. We will make the updated terms available here and give further
          notice when a material change requires it. Philippine law governs these terms, subject to any
          protections that cannot be waived. For questions, corrections, or account concerns, contact
          <a className="ml-1 font-medium text-blue-700 underline-offset-2 hover:underline" href="mailto:lanes@navlanes.live">lanes@navlanes.live</a>.
        </p>
      </LegalSection>
    </div>
  );
}
