import { LegalSection } from "./LegalSection";

export function PrivacyContent() {
  return (
    <div className="space-y-7 text-sm leading-6 text-slate-700 sm:text-base sm:leading-7">
      <LegalSection id="who-we-are" title="1. Who is responsible for your data">
        <p>
          The LANES Project team operates this flood information, community reporting, and navigation service.
          LANES was developed as a capstone project at Pamantasan ng Lungsod ng Pasig; that academic
          affiliation does not mean the university operates this service. For privacy questions or requests,
          email <a className="font-medium text-blue-700 underline-offset-2 hover:underline" href="mailto:lanes@navlanes.live">lanes@navlanes.live</a>.
        </p>
      </LegalSection>

      <LegalSection id="data-we-collect" title="2. Personal data we handle">
        <ul className="list-disc space-y-2 pl-5">
          <li><strong>Account and identity:</strong> username, email address, password hash, verification information, and, if you choose Google sign in, the name, email address, and profile photo Google provides.</li>
          <li><strong>Profile and saved places:</strong> name, optional contact number, birthdate, address, profile photo, visibility choices, and the names and coordinates of places you save.</li>
          <li><strong>Contributions:</strong> flood report descriptions, locations, photos, community posts, comments, reactions, and moderation or correction history. Text and images you submit may contain personal details about you or others.</li>
          <li><strong>Location and routing:</strong> locations you enter or select, and your device location only when you allow browser location access. Route start and destination coordinates are used to calculate a route.</li>
          <li><strong>Use and security:</strong> a browser generated visitor identifier stored locally, a server generated daily hash for visitor counts, account activity and security audit records, and technical information such as IP address and browser details that may appear in server logs.</li>
          <li><strong>Messages:</strong> your name, email address, subject, and message when you contact the team.</li>
        </ul>
        <p>You can view the public map without creating an account. Some features, including posting and saved places, require one.</p>
      </LegalSection>

      <LegalSection id="purposes" title="3. Why we use data and our lawful grounds">
        <p>
          We use account, profile, and location information to provide the features you request: registration,
          sign in, saved places, map routes, reports, and community participation. We use contact details to
          send verification and account messages and to answer inquiries. These activities are necessary to
          provide the requested service or take steps you request before using it.
        </p>
        <p>
          We review reports, prevent abuse, protect accounts, keep audit records, and count visits to operate
          and improve LANES. Where applicable, this processing is based on legitimate interests that are
          balanced against your rights, or on legal obligations. Optional device location access depends on
          your browser permission; you can withdraw that permission in your device or browser settings.
          Where a separate activity requires consent under Philippine law, we will ask for it before that activity.
        </p>
      </LegalSection>

      <LegalSection id="public-and-automated" title="4. Public content and automated processing">
        <p>
          Posts, comments, approved flood reports, submitted media, location tags, and the profile details
          allowed by your visibility settings may be shown to other users or the public. Avoid adding private
          details about yourself or someone else to public submissions. You can change available profile
          visibility settings, and you may ask us to review or remove content through the contact address above.
        </p>
        <p>
          LANES uses software to extract locations and flood details, check duplicate or conflicting claims,
          calculate map zones and routes, and support moderation. Eligible news claims may be published as
          source labeled alerts or estimated zones after automated checks. Citizen reports follow a staff
          review process. You may ask us to review an inaccurate report, location, or automated result.
        </p>
      </LegalSection>

      <LegalSection id="sharing" title="5. Who may receive data">
        <p>Access is limited to what is needed for each purpose. Recipients may include:</p>
        <ul className="list-disc space-y-2 pl-5">
          <li>LANES administrators and moderators who handle accounts, reports, safety, and support;</li>
          <li>hosting and database providers, Cloudinary for uploaded images, and email delivery providers for verification and contact messages;</li>
          <li>Google if you choose Google sign in, and map or routing providers when their services are used, which may receive requested map areas or route coordinates; and</li>
          <li>other users and the public for content you publish or that is approved for public display, or authorities where disclosure is required by law.</li>
        </ul>
        <p>
          Some providers may process information outside the Philippines. We remain responsible for handling
          personal data in accordance with applicable law when using service providers. LANES does not offer
          your personal data for sale.
        </p>
      </LegalSection>

      <LegalSection id="storage" title="6. Storage, retention, and security">
        <p>
          Account and profile information is kept while your account is active and for any further period
          needed to resolve a request, dispute, or legal obligation. Saved places remain until you remove them
          or your account is removed. Public posts and flood reports can remain while they are needed for
          community information, safety review, or a documented moderation or audit purpose. Visitor and
          security records are kept only while needed for analytics, abuse prevention, and legal or operational
          requirements. We review data for deletion or de-identification when those purposes end; copies in
          backups may remain until the relevant backup is replaced.
        </p>
        <p>
          We use access controls, password hashing, and other reasonable technical and organizational
          safeguards. No online service can promise absolute security. If an incident requires notification,
          we will notify affected people and the National Privacy Commission as required by law.
        </p>
        <p>
          Your browser may store your login token, visitor identifier, map data for offline use, and session
          preferences. Signing out removes the login token; browser settings can clear locally stored data.
        </p>
      </LegalSection>

      <LegalSection id="rights" title="7. Your data privacy rights">
        <p>
          Under Republic Act No. 10173 and its implementing rules, you may request information about our
          processing; access or correction of your data; object to processing; withdrawal of consent where
          consent is the basis; erasure or blocking when legally available; and a portable copy of qualifying
          electronic data. You may also seek damages and file a complaint with the National Privacy Commission.
        </p>
        <p>
          Email <a className="font-medium text-blue-700 underline-offset-2 hover:underline" href="mailto:lanes@navlanes.live">lanes@navlanes.live</a> to make a request.
          Tell us which account or content is involved. We may verify your identity before releasing or changing
          data, and we will explain if a legal or safety reason limits a request. You can also contact the
          <a className="ml-1 font-medium text-blue-700 underline-offset-2 hover:underline" href="https://privacy.gov.ph/data-subject-rights/">National Privacy Commission</a>.
        </p>
      </LegalSection>

      <LegalSection id="changes" title="8. Updates to this notice">
        <p>
          We will update this notice when our data practices change and change the date above. Where a change
          materially affects how your data is used, we will provide further notice or seek consent when required.
          The Terms of Service explain how to use LANES.
        </p>
        <p className="text-sm text-slate-600">
          Legal references: <a className="text-blue-700 underline-offset-2 hover:underline" href="https://privacy.gov.ph/Data-Privacy-Act/">Data Privacy Act of 2012</a>
          {" and "}<a className="text-blue-700 underline-offset-2 hover:underline" href="https://privacy.gov.ph/implementing-rules%20regulations-data-privacy-act-2012/">its Implementing Rules and Regulations</a>.
        </p>
      </LegalSection>
    </div>
  );
}
