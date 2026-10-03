/**
 * Diccionario y utilidades de geolocalización para vacantes en República Dominicana.
 * Provee coordenadas precisas (latitud, longitud) para cada municipio, provincia o sector.
 */

export const COORDENADAS_RD = {
    // Santo Domingo y Distrito Nacional
    'piantini': { lat: 18.4740, lng: -69.9360 },
    'naco': { lat: 18.4764, lng: -69.9270 },
    'bella vista': { lat: 18.4550, lng: -69.9500 },
    'el millón': { lat: 18.4687, lng: -69.9472 },
    'el millon': { lat: 18.4687, lng: -69.9472 },
    'sector renacimiento': { lat: 18.4485, lng: -69.9675 },
    'renacimiento': { lat: 18.4485, lng: -69.9675 },
    'winston churchill': { lat: 18.4719, lng: -69.9405 },
    'abraham lincoln': { lat: 18.4690, lng: -69.9300 },
    'ciudad nueva': { lat: 18.4716, lng: -69.8890 },
    'zona colonial': { lat: 18.4735, lng: -69.8856 },
    'gazcue': { lat: 18.4689, lng: -69.8972 },
    'villa juana': { lat: 18.4900, lng: -69.9100 },
    'los próceres': { lat: 18.4912, lng: -69.9550 },
    'herrera': { lat: 18.4682, lng: -69.9733 },
    'santo domingo oeste': { lat: 18.4905, lng: -69.9912 },
    'santo domingo este': { lat: 18.4884, lng: -69.8571 },
    'san isidro': { lat: 18.5200, lng: -69.8000 },
    'alma rosa': { lat: 18.4920, lng: -69.8650 },
    'santo domingo norte': { lat: 18.5447, lng: -69.9048 },
    'villa mella': { lat: 18.5447, lng: -69.9048 },
    'los alcarrizos': { lat: 18.5173, lng: -70.0152 },
    'distrito nacional': { lat: 18.4861, lng: -69.9312 },
    'santo domingo': { lat: 18.4861, lng: -69.9312 },

    // Región Este
    'bávaro': { lat: 18.6813, lng: -68.4443 },
    'bavaro': { lat: 18.6813, lng: -68.4443 },
    'punta cana': { lat: 18.5601, lng: -68.3725 },
    'la romana': { lat: 18.4273, lng: -68.9728 },
    'san pedro de macorís': { lat: 18.4539, lng: -69.3038 },
    'san pedro de macoris': { lat: 18.4539, lng: -69.3038 },
    'higüey': { lat: 18.6150, lng: -68.7070 },
    'higuey': { lat: 18.6150, lng: -68.7070 },
    'boca chica': { lat: 18.4500, lng: -69.6000 },
    'haina': { lat: 18.4190, lng: -70.0270 },

    // Región Norte / Cibao
    'hato del yaque': { lat: 19.4358, lng: -70.7672 },
    'santiago de los caballeros': { lat: 19.4517, lng: -70.6970 },
    'santiago': { lat: 19.4517, lng: -70.6970 },
    'la vega': { lat: 19.2220, lng: -70.5296 },
    'san francisco de macorís': { lat: 19.3000, lng: -70.2500 },
    'san francisco de macoris': { lat: 19.3000, lng: -70.2500 },
    'puerto plata': { lat: 19.7934, lng: -70.6884 },
    'bonao': { lat: 18.9460, lng: -70.4090 },
    'moca': { lat: 19.3930, lng: -70.5250 },

    // Región Sur
    'san cristóbal': { lat: 18.4167, lng: -70.1000 },
    'san cristobal': { lat: 18.4167, lng: -70.1000 },
    'baní': { lat: 18.2796, lng: -70.3318 },
    'bani': { lat: 18.2796, lng: -70.3318 },
    'azua': { lat: 18.4532, lng: -70.7349 },
    'barahona': { lat: 18.2085, lng: -71.1008 },
    'san juan de la maguana': { lat: 18.8059, lng: -71.2299 },
    'san juan': { lat: 18.8059, lng: -71.2299 }
};

/**
 * Resuelve las coordenadas numéricas precisas { lat, lng } para una vacante.
 * @param {Object} payload Datos de la vacante seleccionada
 * @returns {{ lat: number, lng: number }} Coordenadas validadas
 */
export function resolverCoordenadasVacante(payload) {
    if (!payload) {
        return { lat: 18.4861, lng: -69.9312 }; // Santo Domingo por defecto
    }

    // 1. Si la vacante ya trae latitud y longitud explícitas
    const lat = payload.latitud ?? payload.lat;
    const lng = payload.longitud ?? payload.lng ?? payload.lon;

    if (lat !== undefined && lat !== null && lng !== undefined && lng !== null) {
        const numLat = parseFloat(lat);
        const numLng = parseFloat(lng);
        if (!isNaN(numLat) && !isNaN(numLng) && numLat !== 0 && numLng !== 0) {
            return { lat: numLat, lng: numLng };
        }
    }

    // 2. Resolver por texto de Ubicación, Dirección, Sector o Nombre de Empresa
    const textoBuscar = `${payload.Direccion || ''} ${payload.Ubicacion || ''} ${payload.sector || ''} ${payload.Nombre_Empresa || ''}`.toLowerCase();

    for (const [clave, coords] of Object.entries(COORDENADAS_RD)) {
        if (textoBuscar.includes(clave)) {
            return { ...coords };
        }
    }

    // 3. Fallback inteligente a Santo Domingo Centro
    return { lat: 18.4861, lng: -69.9172 };
}
