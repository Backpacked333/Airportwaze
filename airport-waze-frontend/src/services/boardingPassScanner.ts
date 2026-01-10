/**
 * Boarding Pass Scanner Service
 *
 * Automatically extracts flight information from boarding pass:
 * - QR code scanning (IATA Bar Coded Boarding Pass - BCBP)
 * - OCR text recognition (backup)
 * - PDF417 barcode support
 *
 * BCBP Format Example:
 * M1DESMARAIS/LUC       EABC123 YULFRAAC 0834 226F001A0025 100
 */

export interface FlightInfo {
  passengerName?: string;
  bookingReference?: string;
  flightNumber: string;
  airline: string;
  airlineCode: string;
  departureAirport: string;
  arrivalAirport: string;
  departureDate: Date;
  departureTime?: string;
  boardingTime?: Date;
  gate?: string;
  terminal?: string;
  seat?: string;
  sequenceNumber?: string;
}

export interface ScanResult {
  success: boolean;
  flightInfo?: FlightInfo;
  error?: string;
  raw?: string;
}

class BoardingPassScanner {
  private videoStream: MediaStream | null = null;
  private canvas: HTMLCanvasElement | null = null;
  private isScanning: boolean = false;

  /**
   * Start camera and scan for boarding pass
   */
  async startScanning(
    videoElement: HTMLVideoElement,
    onDetected: (result: ScanResult) => void
  ): Promise<void> {
    try {
      // Request camera access
      this.videoStream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: 'environment', // Use back camera on mobile
          width: { ideal: 1920 },
          height: { ideal: 1080 }
        }
      });

      videoElement.srcObject = this.videoStream;
      await videoElement.play();

      this.isScanning = true;
      this.scanLoop(videoElement, onDetected);
    } catch (error) {
      console.error('[BoardingPass] Camera access error:', error);
      onDetected({
        success: false,
        error: 'Camera access denied. Please enable camera permissions.'
      });
    }
  }

  /**
   * Stop scanning and release camera
   */
  stopScanning(videoElement: HTMLVideoElement) {
    this.isScanning = false;

    if (this.videoStream) {
      this.videoStream.getTracks().forEach(track => track.stop());
      this.videoStream = null;
    }

    if (videoElement.srcObject) {
      videoElement.srcObject = null;
    }
  }

  /**
   * Scan loop - analyze video frames for QR codes/barcodes
   */
  private async scanLoop(
    videoElement: HTMLVideoElement,
    onDetected: (result: ScanResult) => void
  ) {
    if (!this.isScanning) return;

    // Create canvas for frame capture
    if (!this.canvas) {
      this.canvas = document.createElement('canvas');
    }

    this.canvas.width = videoElement.videoWidth;
    this.canvas.height = videoElement.videoHeight;

    const context = this.canvas.getContext('2d');
    if (!context) return;

    // Capture frame
    context.drawImage(videoElement, 0, 0);

    try {
      // Try to detect QR code using built-in BarcodeDetector API
      if ('BarcodeDetector' in window) {
        const barcodeDetector = new (window as any).BarcodeDetector({
          formats: ['qr_code', 'pdf417', 'aztec']
        });

        const barcodes = await barcodeDetector.detect(this.canvas);

        if (barcodes.length > 0) {
          const rawData = barcodes[0].rawValue;
          console.log('[BoardingPass] Detected:', rawData);

          const result = this.parseBoardingPass(rawData);
          onDetected(result);

          if (result.success) {
            this.stopScanning(videoElement);
            return;
          }
        }
      }
    } catch (error) {
      console.error('[BoardingPass] Detection error:', error);
    }

    // Continue scanning
    setTimeout(() => this.scanLoop(videoElement, onDetected), 100);
  }

  /**
   * Parse IATA Bar Coded Boarding Pass (BCBP) format
   *
   * Format: M1LASTNAME/FIRSTNAME EBKREF DEPARVAIRLINE FLIGHTNO JULIANDAY SEATCLASS SEQNO
   */
  parseBoardingPass(rawData: string): ScanResult {
    try {
      // Check if it's BCBP format (starts with M1 or M2)
      if (!rawData.startsWith('M1') && !rawData.startsWith('M2')) {
        // Try alternative formats
        return this.parseAlternativeFormat(rawData);
      }

      // Remove format version
      const data = rawData.substring(2);

      // Parse passenger name (variable length, space-padded to 20 chars)
      const passengerNameMatch = data.match(/^([A-Z\/\s]{1,20})/);
      const passengerName = passengerNameMatch ? passengerNameMatch[1].trim() : undefined;
      let pos = passengerNameMatch ? passengerNameMatch[0].length : 0;

      // Electronic ticket indicator (E)
      pos += 1;

      // Booking reference (6 chars)
      const bookingReference = data.substring(pos, pos + 6).trim();
      pos += 6;

      // Departure airport (3 chars)
      const departureAirport = data.substring(pos, pos + 3);
      pos += 3;

      // Arrival airport (3 chars)
      const arrivalAirport = data.substring(pos, pos + 3);
      pos += 3;

      // Airline code (3 chars)
      const airlineCode = data.substring(pos, pos + 3);
      pos += 3;

      // Flight number (5 chars, may have leading zeros)
      const flightNumberRaw = data.substring(pos, pos + 5);
      const flightNumber = airlineCode + flightNumberRaw.replace(/^0+/, '');
      pos += 5;

      // Julian date (3 chars)
      const julianDayStr = data.substring(pos, pos + 3);
      const julianDay = parseInt(julianDayStr, 10);
      pos += 3;

      // Cabin class (1 char) + Seat (4 chars)
      const cabinClass = data.substring(pos, pos + 1);
      pos += 1;
      const seat = data.substring(pos, pos + 4).trim();
      pos += 4;

      // Sequence number (5 chars)
      const sequenceNumber = data.substring(pos, pos + 5);
      pos += 5;

      // Convert Julian day to actual date
      const departureDate = this.julianToDate(julianDay);

      // Get airline name from code
      const airline = this.getAirlineName(airlineCode);

      const flightInfo: FlightInfo = {
        passengerName,
        bookingReference,
        flightNumber,
        airline,
        airlineCode,
        departureAirport,
        arrivalAirport,
        departureDate,
        seat,
        sequenceNumber
      };

      return {
        success: true,
        flightInfo,
        raw: rawData
      };
    } catch (error) {
      console.error('[BoardingPass] Parse error:', error);
      return {
        success: false,
        error: 'Could not parse boarding pass. Please enter flight details manually.',
        raw: rawData
      };
    }
  }

  /**
   * Parse alternative formats (e.g., custom airline formats)
   */
  private parseAlternativeFormat(rawData: string): ScanResult {
    // Try JSON format (some airlines use JSON in QR codes)
    try {
      const json = JSON.parse(rawData);
      if (json.flightNumber || json.flight) {
        return {
          success: true,
          flightInfo: {
            flightNumber: json.flightNumber || json.flight,
            airline: json.airline || 'Unknown',
            airlineCode: json.airlineCode || json.carrier || 'XX',
            departureAirport: json.origin || json.from || 'XXX',
            arrivalAirport: json.destination || json.to || 'XXX',
            departureDate: json.date ? new Date(json.date) : new Date(),
            gate: json.gate,
            terminal: json.terminal,
            seat: json.seat
          },
          raw: rawData
        };
      }
    } catch {}

    // Try simple text parsing (flight number extraction)
    const flightMatch = rawData.match(/([A-Z]{2})\s?(\d{1,4})/);
    if (flightMatch) {
      const airlineCode = flightMatch[1];
      const flightNum = flightMatch[2];

      return {
        success: true,
        flightInfo: {
          flightNumber: airlineCode + flightNum,
          airline: this.getAirlineName(airlineCode),
          airlineCode,
          departureAirport: 'XXX',
          arrivalAirport: 'XXX',
          departureDate: new Date()
        },
        raw: rawData
      };
    }

    return {
      success: false,
      error: 'Unrecognized boarding pass format',
      raw: rawData
    };
  }

  /**
   * Convert Julian day to actual date
   */
  private julianToDate(julianDay: number): Date {
    const year = new Date().getFullYear();
    const date = new Date(year, 0, julianDay);
    return date;
  }

  /**
   * Get airline name from IATA code
   */
  private getAirlineName(code: string): string {
    const airlines: Record<string, string> = {
      'AA': 'American Airlines',
      'UA': 'United Airlines',
      'DL': 'Delta Air Lines',
      'WN': 'Southwest Airlines',
      'B6': 'JetBlue Airways',
      'AS': 'Alaska Airlines',
      'NK': 'Spirit Airlines',
      'F9': 'Frontier Airlines',
      'G4': 'Allegiant Air',
      'SY': 'Sun Country Airlines',
      'AC': 'Air Canada',
      'BA': 'British Airways',
      'LH': 'Lufthansa',
      'AF': 'Air France',
      'KL': 'KLM',
      'EK': 'Emirates',
      'QR': 'Qatar Airways',
      'SQ': 'Singapore Airlines',
      'CX': 'Cathay Pacific',
      'JL': 'Japan Airlines',
      'NH': 'All Nippon Airways'
    };

    return airlines[code] || code;
  }

  /**
   * Manual entry fallback
   */
  createManualEntry(
    flightNumber: string,
    departureAirport: string,
    departureDate: Date,
    gate?: string,
    terminal?: string
  ): FlightInfo {
    const airlineCode = flightNumber.match(/^([A-Z]{2})/)?.[1] || 'XX';

    return {
      flightNumber,
      airline: this.getAirlineName(airlineCode),
      airlineCode,
      departureAirport,
      arrivalAirport: 'XXX', // Unknown
      departureDate,
      gate,
      terminal
    };
  }
}

// Export singleton
export const boardingPassScanner = new BoardingPassScanner();
