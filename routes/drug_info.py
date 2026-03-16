from fastapi import APIRouter, HTTPException, Query
import httpx
from typing import List

router = APIRouter(tags=["Drug & Disease Info"])

PUBCHEM_BASE = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
UNIPROT_BASE = "https://rest.uniprot.org"
OPENFDA_BASE = "https://api.fda.gov/drug"


@router.get("/drug-info")
async def get_drug_info(name: str = Query(..., description="Drug or compound name")):
    """Fetch drug/molecule information from PubChem API"""
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            # Search for compound CID
            search_url = f"{PUBCHEM_BASE}/compound/name/{name}/JSON"
            resp = await client.get(search_url)

            if resp.status_code == 404:
                raise HTTPException(status_code=404, detail=f"No compound found for '{name}'")

            data = resp.json()
            compounds = data.get("PC_Compounds", [])
            if not compounds:
                raise HTTPException(status_code=404, detail="No compound data found")

            compound = compounds[0]
            cid = compound.get("id", {}).get("id", {}).get("cid", "N/A")

            # Extract properties
            props = {}
            for prop in compound.get("props", []):
                urn = prop.get("urn", {})
                label = urn.get("label", "")
                name_key = urn.get("name", "")
                val = prop.get("value", {})

                if label == "Molecular Formula":
                    props["molecular_formula"] = val.get("sval", "")
                elif label == "Molecular Weight":
                    props["molecular_weight"] = val.get("fval", val.get("sval", ""))
                elif label == "IUPAC Name" and name_key == "Preferred":
                    props["iupac_name"] = val.get("sval", "")
                elif label == "InChI":
                    props["inchi"] = val.get("sval", "")
                elif label == "SMILES" and name_key == "Canonical":
                    props["canonical_smiles"] = val.get("sval", "")
                elif label == "Log P":
                    props["logp"] = val.get("fval", "")
                elif label == "Hydrogen Bond Donor Count":
                    props["h_bond_donors"] = val.get("ival", "")
                elif label == "Hydrogen Bond Acceptor Count":
                    props["h_bond_acceptors"] = val.get("ival", "")
                elif label == "Rotatable Bond Count":
                    props["rotatable_bonds"] = val.get("ival", "")

            # Get 2D image URL
            image_url = f"{PUBCHEM_BASE}/compound/CID/{cid}/PNG"

            # Fetch FDA safety data
            fda_url = f"{OPENFDA_BASE}/label.json?search=openfda.generic_name:{name}&limit=1"
            fda_resp = await client.get(fda_url)
            fda_info = {}
            if fda_resp.status_code == 200:
                fda_data = fda_resp.json()
                results = fda_data.get("results", [])
                if results:
                    r = results[0]
                    fda_info = {
                        "warnings": r.get("warnings", ["N/A"])[:3] if r.get("warnings") else [],
                        "indications": r.get("indications_and_usage", ["N/A"])[:2] if r.get("indications_and_usage") else [],
                        "adverse_reactions": r.get("adverse_reactions", ["N/A"])[:2] if r.get("adverse_reactions") else []
                    }

            return {
                "name": name,
                "cid": cid,
                "structure_image": image_url,
                "properties": props,
                "fda_info": fda_info
            }

        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"External API error: {str(e)}")


@router.get("/disease-info")
async def get_disease_info(disease: str = Query(..., description="Disease name")):
    """Fetch protein and disease data from UniProt API"""
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            # Search UniProt for proteins related to disease
            uniprot_url = f"{UNIPROT_BASE}/uniprotkb/search"
            params = {
                "query": f"cc_disease:{disease} AND reviewed:true",
                "format": "json",
                "size": 10,
                "fields": "accession,protein_name,gene_names,organism_name,cc_disease,sequence"
            }

            resp = await client.get(uniprot_url, params=params)

            if resp.status_code != 200:
                # Try broader search
                params["query"] = f"{disease} AND reviewed:true"
                resp = await client.get(uniprot_url, params=params)

            data = resp.json()
            results = data.get("results", [])

            proteins = []
            for entry in results[:8]:
                protein_name = entry.get("proteinDescription", {})
                recommended = protein_name.get("recommendedName", {})
                full_name = recommended.get("fullName", {}).get("value", "Unknown Protein")

                genes = entry.get("genes", [])
                gene_names = [g.get("geneName", {}).get("value", "") for g in genes if g.get("geneName")]

                diseases = []
                for comment in entry.get("comments", []):
                    if comment.get("commentType") == "DISEASE":
                        d = comment.get("disease", {})
                        diseases.append(d.get("diseaseId", d.get("diseaseAcronym", "Unknown")))

                proteins.append({
                    "accession": entry.get("primaryAccession", ""),
                    "protein_name": full_name,
                    "gene_names": gene_names,
                    "organism": entry.get("organism", {}).get("scientificName", ""),
                    "related_diseases": diseases,
                    "uniprot_link": f"https://www.uniprot.org/uniprotkb/{entry.get('primaryAccession', '')}"
                })

            # Also fetch FDA drug events for disease
            fda_events_url = f"{OPENFDA_BASE}/event.json?search=patient.reaction.reactionmeddrapt:{disease}&limit=5"
            fda_events = []
            try:
                fda_resp = await client.get(fda_events_url)
                if fda_resp.status_code == 200:
                    fda_data = fda_resp.json()
                    for event in fda_data.get("results", [])[:5]:
                        drugs = event.get("patient", {}).get("drug", [])
                        for drug in drugs[:2]:
                            drug_name = drug.get("medicinalproduct", "Unknown Drug")
                            if drug_name not in fda_events:
                                fda_events.append(drug_name)
            except Exception:
                pass

            # Get unique drugs (up to 10)
            unique_fda_drugs = []
            for drug in fda_events:
                if drug not in unique_fda_drugs:
                    unique_fda_drugs.append(drug)
                    if len(unique_fda_drugs) >= 10:
                        break

            return {
                "disease": disease,
                "protein_count": len(proteins),
                "proteins": proteins,
                "drugs_reported_in_fda": unique_fda_drugs
            }

        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"External API error: {str(e)}")
