import React from "react";
import "./Styles/NavSections.css";
import { NAV_SECTIONS } from "../navSectionsConfig";

export default function NavSections({
  sections = NAV_SECTIONS,
  activeSection,
  onSelectSection,
}) {
  return (
    <div className="Nav-Sections">
      {sections.map((sec, index) => {
        const id = typeof sec === "string" ? sec : sec.id;
        const label = typeof sec === "string" ? sec : sec.label || sec.id;
        const isActive = activeSection === id;
        return (
          <div
            key={id || index}
            className={`Nav-Section-Item ${isActive ? "active" : ""}`}
            onClick={() => onSelectSection && onSelectSection(id)}
          >
            {label}
          </div>
        );
      })}
    </div>
  );
}
