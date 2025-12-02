export const generatedData = {
  "project_id": "aae047bd-c5af-4bef-8a5b-22d001235289",
  "generation_id": "9861b9e7-73c3-438d-afe7-d255f3618e66",
  "schema": {
    "type": "Root",
    "props": {
      "className": "flex flex-col min-h-screen font-inter bg-neutral-50"
    },
    "children": [
      {
        "type": "Header",
        "props": {
          "className": "sticky top-0 z-50 bg-white shadow-lg backdrop-blur-md bg-opacity-90"
        },
        "children": [
          {
            "type": "Text",
            "props": {
              "tag": "h1",
              "className": "text-2xl font-bold text-[#0C66E4]"
            },
            "content": "Dr. E. Vance"
          },
          {
            "type": "Navigation",
            "props": {
              "className": "hidden md:flex space-x-6 text-gray-700 font-medium"
            },
            "children": [
              {"type": "Link/A", "props": {"href": "#about", "className": "hover:text-[#0C66E4] transition duration-300"}, "content": "About"},
              {"type": "Link/A", "props": {"href": "#specialties", "className": "hover:text-[#0C66E4] transition duration-300"}, "content": "Specialties"},
              {"type": "Link/A", "props": {"href": "#credentials", "className": "hover:text-[#0C66E4] transition duration-300"}, "content": "Credentials"},
              {"type": "Link/A", "props": {"href": "#testimonials", "className": "hover:text-[#0C66E4] transition duration-300"}, "content": "Testimonials"},
              {"type": "Button", "props": {"href": "#contact", "className": "px-4 py-2 rounded-full bg-[#10B981] text-white hover:bg-emerald-600 shadow-md"}, "content": "Book Consult"}
            ]
          }
        ]
      },
      {
        "type": "Section",
        "props": {
          "id": "hero",
          "className": "py-16 md:py-24 bg-white container-padding grid md:grid-cols-2 gap-12 items-center max-w-7xl mx-auto"
        },
        "children": [
          {
            "type": "Div",
            "props": {},
            "children": [
              {
                "type": "Text",
                "props": {
                  "tag": "span",
                  "className": "inline-block px-3 py-1 text-sm font-semibold rounded-full bg-[#0C66E4] text-white mb-4 shadow-lg"
                },
                "content": "Orthopedic Sports Medicine"
              },
              {
                "type": "Text",
                "props": {
                  "tag": "h1",
                  "className": "text-5xl md:text-6xl font-extrabold leading-tight text-gray-900 mb-6"
                },
                "content": "Get Back in the Game. "
              },
              {
                "type": "Text",
                "props": {
                  "tag": "span",
                  "className": "text-[#0C66E4]"
                },
                "content": "Stronger."
              },
              {
                "type": "Text",
                "props": {
                  "tag": "p",
                  "className": "text-lg text-gray-600 mb-8"
                },
                "content": "Dr. Elias Vance specializes in state-of-the-art diagnostics and personalized treatment plans for athletic and activity-related injuries, from elite athletes to weekend warriors."
              },
              {
                "type": "Div",
                "props": {
                  "className": "flex flex-col sm:flex-row space-y-4 sm:space-y-0 sm:space-x-4"
                },
                "children": [
                  {
                    "type": "Link/A",
                    "props": {
                      "href": "#contact",
                      "icon": "CalendarCheck",
                      "className": "flex items-center justify-center space-x-2 px-8 py-3 bg-[#10B981] text-white font-semibold rounded-xl shadow-xl hover:bg-emerald-600 transition duration-300 transform hover:scale-[1.02]"
                    },
                    "content": "Schedule Appointment"
                  },
                  {
                    "type": "Link/A",
                    "props": {
                      "href": "#specialties",
                      "icon": "Dumbbell",
                      "className": "flex items-center justify-center space-x-2 px-8 py-3 bg-transparent border-2 border-[#0C66E4] text-[#0C66E4] font-semibold rounded-xl hover:bg-[#0C66E4] hover:text-white transition duration-300"
                    },
                    "content": "Explore Specialties"
                  }
                ]
              }
            ]
          },
          {
            "type": "Image",
            "props": {
              "src": "https://placehold.co/600x600/0C66E4/FFFFFF?text=Dr.+Vance+Headshot",
              "alt": "Professional portrait of Dr. Elias Vance",
              "className": "w-full h-auto object-cover rounded-3xl shadow-2xl transform rotate-3 transition duration-500 hidden md:block"
            }
          }
        ]
      },
      {
        "type": "Section",
        "props": {
          "id": "about",
          "className": "py-16 md:py-20 bg-neutral-50 container-padding max-w-7xl mx-auto"
        },
        "children": [
          {
            "type": "Text",
            "props": {
              "tag": "h2",
              "className": "text-4xl font-bold text-center mb-4 text-gray-900"
            },
            "content": "My Philosophy"
          },
          {
            "type": "Text",
            "props": {
              "tag": "p",
              "className": "text-xl text-center text-gray-600 mb-12 max-w-3xl mx-auto"
            },
            "content": "Treating the injury is only the beginning. My goal is complete recovery and prevention of future trauma."
          },
          {
            "type": "Div",
            "props": {
              "className": "grid md:grid-cols-3 gap-8"
            },
            "children": [
              {
                "type": "Card",
                "props": {
                  "icon": "Stethoscope",
                  "className": "bg-white p-8 rounded-2xl shadow-lg border-t-4 border-[#0C66E4] transform hover:scale-[1.02] transition duration-300"
                },
                "children": [
                  {
                    "type": "Icon",
                    "props": {
                      "name": "Stethoscope",
                      "className": "w-8 h-8 text-[#0C66E4] mb-4"
                    }
                  },
                  {
                    "type": "Text",
                    "props": {
                      "tag": "h3",
                      "className": "text-xl font-bold mb-3 text-gray-900"
                    },
                    "content": "Holistic Diagnosis"
                  },
                  {
                    "type": "Text",
                    "props": {
                      "tag": "p",
                      "className": "text-gray-600"
                    },
                    "content": "We look beyond the symptom to identify the root biomechanical cause of the injury, ensuring accurate and lasting solutions."
                  }
                ]
              },
              {
                "type": "Card",
                "props": {
                  "icon": "ScanLine",
                  "className": "bg-white p-8 rounded-2xl shadow-lg border-t-4 border-[#10B981] transform hover:scale-[1.02] transition duration-300"
                },
                "children": [
                  {
                    "type": "Icon",
                    "props": {
                      "name": "ScanLine",
                      "className": "w-8 h-8 text-[#10B981] mb-4"
                    }
                  },
                  {
                    "type": "Text",
                    "props": {
                      "tag": "h3",
                      "className": "text-xl font-bold mb-3 text-gray-900"
                    },
                    "content": "Advanced Techniques"
                  },
                  {
                    "type": "Text",
                    "props": {
                      "tag": "p",
                      "className": "text-gray-600"
                    },
                    "content": "Utilizing the latest in regenerative medicine, minimally invasive surgery, and targeted rehabilitation protocols."
                  }
                ]
              },
              {
                "type": "Card",
                "props": {
                  "icon": "Handshake",
                  "className": "bg-white p-8 rounded-2xl shadow-lg border-t-4 border-[#0C66E4] transform hover:scale-[1.02] transition duration-300"
                },
                "children": [
                  {
                    "type": "Icon",
                    "props": {
                      "name": "Handshake",
                      "className": "w-8 h-8 text-[#0C66E4] mb-4"
                    }
                  },
                  {
                    "type": "Text",
                    "props": {
                      "tag": "h3",
                      "className": "text-xl font-bold mb-3 text-gray-900"
                    },
                    "content": "Collaborative Care"
                  },
                  {
                    "type": "Text",
                    "props": {
                      "tag": "p",
                      "className": "text-gray-600"
                    },
                    "content": "Working closely with physical therapists, trainers, and coaches to guide you through every stage of recovery."
                  }
                ]
              }
            ]
          }
        ]
      },
      {
        "type": "Section",
        "props": {
          "id": "specialties",
          "className": "py-16 md:py-20 bg-white container-padding max-w-7xl mx-auto"
        },
        "children": [
          {
            "type": "Text",
            "props": {
              "tag": "h2",
              "className": "text-4xl font-bold text-center mb-4 text-gray-900"
            },
            "content": "Key Areas of Expertise"
          },
          {
            "type": "Text",
            "props": {
              "tag": "p",
              "className": "text-xl text-center text-gray-600 mb-12 max-w-3xl mx-auto"
            },
            "content": "Specializing in injuries unique to high-impact sports and repetitive motion."
          },
          {
            "type": "Div",
            "props": {
              "className": "grid sm:grid-cols-2 lg:grid-cols-4 gap-8"
            },
            "children": [
              {
                "type": "Card",
                "props": {
                  "className": "p-6 bg-gray-50 rounded-xl shadow-md border border-gray-100 hover:border-[#0C66E4] transition duration-300"
                },
                "children": [
                  {
                    "type": "Icon",
                    "props": {
                      "name": "Bone",
                      "className": "w-6 h-6 text-[#0C66E4] mb-3"
                    }
                  },
                  {
                    "type": "Text",
                    "props": {
                      "tag": "h4",
                      "className": "text-lg font-semibold mb-2 text-gray-900"
                    },
                    "content": "Knee & ACL Injuries"
                  },
                  {
                    "type": "Text",
                    "props": {
                      "tag": "p",
                      "className": "text-sm text-gray-600"
                    },
                    "content": "Specialized focus on complex ligament reconstruction and meniscus repair for athletes."
                  }
                ]
              },
              {
                "type": "Card",
                "props": {
                  "className": "p-6 bg-gray-50 rounded-xl shadow-md border border-gray-100 hover:border-[#0C66E4] transition duration-300"
                },
                "children": [
                  {
                    "type": "Icon",
                    "props": {
                      "name": "Armchair",
                      "className": "w-6 h-6 text-[#0C66E4] mb-3"
                    }
                  },
                  {
                    "type": "Text",
                    "props": {
                      "tag": "h4",
                      "className": "text-lg font-semibold mb-2 text-gray-900"
                    },
                    "content": "Shoulder & Rotator Cuff"
                  },
                  {
                    "type": "Text",
                    "props": {
                      "tag": "p",
                      "className": "text-sm text-gray-600"
                    },
                    "content": "Advanced treatment for instability, labral tears, and rotator cuff pathology."
                  }
                ]
              },
              {
                "type": "Card",
                "props": {
                  "className": "p-6 bg-gray-50 rounded-xl shadow-md border border-gray-100 hover:border-[#0C66E4] transition duration-300"
                },
                "children": [
                  {
                    "type": "Icon",
                    "props": {
                      "name": "BrainCircuit",
                      "className": "w-6 h-6 text-[#0C66E4] mb-3"
                    }
                  },
                  {
                    "type": "Text",
                    "props": {
                      "tag": "h4",
                      "className": "text-lg font-semibold mb-2 text-gray-900"
                    },
                    "content": "Concussion Management"
                  },
                  {
                    "type": "Text",
                    "props": {
                      "tag": "p",
                      "className": "text-sm text-gray-600"
                    },
                    "content": "Evidence-based \"Return to Play\" protocols and neurological clearance."
                  }
                ]
              },
              {
                "type": "Card",
                "props": {
                  "className": "p-6 bg-gray-50 rounded-xl shadow-md border border-gray-100 hover:border-[#0C66E4] transition duration-300"
                },
                "children": [
                  {
                    "type": "Icon",
                    "props": {
                      "name": "Footprints",
                      "className": "w-6 h-6 text-[#0C66E4] mb-3"
                    }
                  },
                  {
                    "type": "Text",
                    "props": {
                      "tag": "h4",
                      "className": "text-lg font-semibold mb-2 text-gray-900"
                    },
                    "content": "Ankle & Foot Trauma"
                  },
                  {
                    "type": "Text",
                    "props": {
                      "tag": "p",
                      "className": "text-sm text-gray-600"
                    },
                    "content": "Expert care for Achilles tendon ruptures, complex ankle sprains, and fractures."
                  }
                ]
              }
            ]
          },
          {
            "type": "Div",
            "props": {
              "className": "text-center mt-12"
            },
            "children": [
              {
                "type": "Link/A",
                "props": {
                  "href": "#contact",
                  "className": "px-8 py-3 bg-[#0C66E4] text-white font-semibold rounded-xl shadow-xl hover:bg-primary-dark transition duration-300"
                },
                "content": "See Full Service List"
              }
            ]
          }
        ]
      },
      {
        "type": "Section",
        "props": {
          "id": "credentials",
          "className": "py-16 md:py-20 bg-neutral-100 container-padding max-w-7xl mx-auto"
        },
        "children": [
          {
            "type": "Text",
            "props": {
              "tag": "h2",
              "className": "text-4xl font-bold text-center mb-12 text-gray-900"
            },
            "content": "Education & Credentials"
          },
          {
            "type": "List",
            "props": {
              "className": "max-w-4xl mx-auto space-y-6"
            },
            "children": [
              {
                "type": "ListItem",
                "props": {
                  "className": "p-4 bg-white rounded-lg shadow-md border-l-4 border-[#0C66E4]"
                },
                "children": [
                  {
                    "type": "Text",
                    "props": {
                      "tag": "h3",
                      "className": "text-lg font-semibold text-gray-900"
                    },
                    "content": "Fellowship in Sports Orthopedics"
                  },
                  {
                    "type": "Text",
                    "props": {
                      "tag": "p",
                      "className": "text-gray-600"
                    },
                    "content": "Johns Hopkins Hospital | 2014 - 2015"
                  }
                ]
              },
              {
                "type": "ListItem",
                "props": {
                  "className": "p-4 bg-white rounded-lg shadow-md border-l-4 border-[#0C66E4]"
                },
                "children": [
                  {
                    "type": "Text",
                    "props": {
                      "tag": "h3",
                      "className": "text-lg font-semibold text-gray-900"
                    },
                    "content": "Doctor of Medicine (M.D.)"
                  },
                  {
                    "type": "Text",
                    "props": {
                      "tag": "p",
                      "className": "text-gray-600"
                    },
                    "content": "Harvard Medical School | 2010 - 2014"
                  }
                ]
              },
              {
                "type": "ListItem",
                "props": {
                  "className": "p-4 bg-white rounded-lg shadow-md border-l-4 border-[#0C66E4]"
                },
                "children": [
                  {
                    "type": "Text",
                    "props": {
                      "tag": "h3",
                      "className": "text-lg font-semibold text-gray-900"
                    },
                    "content": "B.S. Kinesiology"
                  },
                  {
                    "type": "Text",
                    "props": {
                      "tag": "p",
                      "className": "text-gray-600"
                    },
                    "content": "University of California, Berkeley | 2006 - 2010"
                  }
                ]
              }
            ]
          }
        ]
      },
      {
        "type": "Section",
        "props": {
          "id": "testimonials",
          "className": "py-16 md:py-20 bg-neutral-50 container-padding max-w-7xl mx-auto"
        },
        "children": [
          {
            "type": "Text",
            "props": {
              "tag": "h2",
              "className": "text-4xl font-bold text-center mb-12 text-gray-900"
            },
            "content": "Success Stories"
          },
          {
            "type": "Div",
            "props": {
              "className": "grid md:grid-cols-2 lg:grid-cols-3 gap-8"
            },
            "children": [
              {
                "type": "Card",
                "props": {
                  "className": "bg-white p-6 rounded-2xl shadow-xl border-l-4 border-[#10B981]"
                },
                "children": [
                  {
                    "type": "Icon",
                    "props": {
                      "name": "MessageSquare",
                      "className": "w-6 h-6 text-[#10B981] mb-3"
                    }
                  },
                  {
                    "type": "Text",
                    "props": {
                      "tag": "p",
                      "className": "italic text-gray-700 mb-4"
                    },
                    "content": "\"After my rotator cuff surgery, I thought my cycling career was over. Dr. Vance's surgical skill and personalized rehab plan had me back on the road training in record time. Truly exceptional care.\""
                  },
                  {
                    "type": "Text",
                    "props": {
                      "tag": "div",
                      "className": "font-semibold text-gray-900"
                    },
                    "content": "- Alex R., Professional Cyclist"
                  }
                ]
              },
              {
                "type": "Card",
                "props": {
                  "className": "bg-white p-6 rounded-2xl shadow-xl border-l-4 border-[#10B981]"
                },
                "children": [
                  {
                    "type": "Icon",
                    "props": {
                      "name": "MessageSquare",
                      "className": "w-6 h-6 text-[#10B981] mb-3"
                    }
                  },
                  {
                    "type": "Text",
                    "props": {
                      "tag": "p",
                      "className": "italic text-gray-700 mb-4"
                    },
                    "content": "\"The most thorough concussion evaluation I've ever received. He didn't just clear me; he gave me the tools to prevent future head trauma. Highly recommend to any high-school athlete.\""
                  },
                  {
                    "type": "Text",
                    "props": {
                      "tag": "div",
                      "className": "font-semibold text-gray-900"
                    },
                    "content": "- Jessica L., Lacrosse Player"
                  }
                ]
              },
              {
                "type": "Card",
                "props": {
                  "className": "bg-white p-6 rounded-2xl shadow-xl border-l-4 border-[#10B981] hidden lg:block"
                },
                "children": [
                  {
                    "type": "Icon",
                    "props": {
                      "name": "MessageSquare",
                      "className": "w-6 h-6 text-[#10B981] mb-3"
                    }
                  },
                  {
                    "type": "Text",
                    "props": {
                      "tag": "p",
                      "className": "italic text-gray-700 mb-4"
                    },
                    "content": "\"I had a complicated Achilles rupture, and Dr. Vance handled the surgery with such precision. His team's post-op support was fantastic. I'm now running marathons again!\""
                  },
                  {
                    "type": "Text",
                    "props": {
                      "tag": "div",
                      "className": "font-semibold text-gray-900"
                    },
                    "content": "- Mark S., Recreational Runner"
                  }
                ]
              }
            ]
          }
        ]
      },
      {
        "type": "Section",
        "props": {
          "id": "contact",
          "className": "py-16 md:py-20 bg-[#0C66E4] container-padding max-w-7xl mx-auto grid lg:grid-cols-2 gap-12 items-center"
        },
        "children": [
          {
            "type": "Div",
            "props": {
              "className": "text-white"
            },
            "children": [
              {
                "type": "Text",
                "props": {
                  "tag": "h2",
                  "className": "text-4xl font-bold mb-4"
                },
                "content": "Ready to Start Your Recovery?"
              },
              {
                "type": "Text",
                "props": {
                  "tag": "p",
                  "className": "text-xl mb-8 opacity-90"
                },
                "content": "Contact our office today to schedule your initial consultation and diagnostic review."
              },
              {
                "type": "Div",
                "props": {
                  "className": "space-y-4"
                },
                "children": [
                  {
                    "type": "Text",
                    "props": {
                      "icon": "MapPin",
                      "className": "flex items-center space-x-3"
                    },
                    "content": "123 Sports Plaza, Suite 400, Cityville, ST 12345"
                  },
                  {
                    "type": "Text",
                    "props": {
                      "icon": "Phone",
                      "className": "flex items-center space-x-3"
                    },
                    "content": "(555) 555-SPORTS (7767)"
                  },
                  {
                    "type": "Text",
                    "props": {
                      "icon": "Mail",
                      "className": "flex items-center space-x-3"
                    },
                    "content": "office@dreliasvance.com"
                  }
                ]
              }
            ]
          },
          {
            "type": "Form",
            "props": {
              "className": "bg-white p-8 rounded-2xl shadow-2xl"
            },
            "children": [
              {
                "type": "Text",
                "props": {
                  "tag": "h3",
                  "className": "text-2xl font-bold mb-6 text-gray-900"
                },
                "content": "Request a Callback"
              },
              {
                "type": "Input",
                "props": {
                  "label": "Full Name",
                  "id": "name",
                  "type": "text",
                  "required": true,
                  "className": "mb-4"
                }
              },
              {
                "type": "Input",
                "props": {
                  "label": "Email or Phone",
                  "id": "email",
                  "type": "text",
                  "required": true,
                  "className": "mb-4"
                }
              },
              {
                "type": "Textarea",
                "props": {
                  "label": "Injury/Issue Summary",
                  "id": "message",
                  "rows": 3,
                  "required": true,
                  "className": "mb-6"
                }
              },
              {
                "type": "Button",
                "props": {
                  "type": "submit",
                  "className": "w-full py-3 bg-[#10B981] text-white font-semibold rounded-xl hover:bg-emerald-600 transition duration-300 shadow-lg"
                },
                "content": "Submit Request"
              }
            ]
          }
        ]
      },
      {
        "type": "Footer",
        "props": {
          "className": "bg-gray-900 py-8"
        },
        "children": [
          {
            "type": "Text",
            "props": {
              "tag": "p",
              "className": "mb-4"
            },
            "content": "© 2025 Dr. Elias Vance. All Rights Reserved. | Orthopedic Sports Medicine"
          },
          {
            "type": "Div",
            "props": {
              "className": "flex justify-center space-x-6"
            },
            "children": [
              {
                "type": "Link/A",
                "props": {
                  "href": "#",
                  "icon": "Linkedin",
                  "className": "hover:text-[#0C66E4] transition duration-300"
                }
              },
              {
                "type": "Link/A",
                "props": {
                  "href": "#",
                  "icon": "Instagram",
                  "className": "hover:text-[#0C66E4] transition duration-300"
                }
              },
              {
                "type": "Link/A",
                "props": {
                  "href": "#",
                  "icon": "Twitter",
                  "className": "hover:text-[#0C66E4] transition duration-300"
                }
              }
            ]
          }
        ]
      }
    ]
  },
  "code": "import React from 'react';\n\nexport default function GeneratedUI() {\n  return (\n  <main className=\"flex flex-col min-h-screen p-6 md:p-12 lg:p-24 bg-neutral-50\">\n    <section className=\"flex flex-col items-center justify-center mb-12\">\n      <img src=\"/doctor-profile.jpg\" alt=\"Doctor's Profile Picture\"  className=\"w-48 h-48 rounded-full mb-4\" />\n      <p className=\"text-4xl font-bold text-neutral-900 mb-2\">Dr. John Doe</p>\n      <p className=\"text-lg text-neutral-600\">Cardiothoracic Surgeon</p>\n    </section>\n    <section className=\"flex flex-col mb-12\">\n      <p className=\"text-3xl font-bold text-neutral-900 mb-4\">About Me</p>\n      <p className=\"text-lg text-neutral-600 leading-relaxed\">Dr. John Doe is a highly skilled cardiothoracic surgeon with over 10 years of experience in the field. He has performed numerous surgeries and has a proven track record of success.</p>\n    </section>\n    <section className=\"flex flex-col mb-12\">\n      <p className=\"text-3xl font-bold text-neutral-900 mb-4\">Education and Training</p>\n      <div className=\"mb-4\">\n        <div className=\"flex items-center gap-2 mb-2\">\n          <p className=\"text-lg text-neutral-600\">MBBS, University of Medicine (2005-2011)</p>\n        </div>\n        <div className=\"flex items-center gap-2 mb-2\">\n          <p className=\"text-lg text-neutral-600\">MS, Cardiothoracic Surgery, University of Surgery (2012-2014)</p>\n        </div>\n      </div>\n    </section>\n    <section className=\"flex flex-col mb-12\">\n      <p className=\"text-3xl font-bold text-neutral-900 mb-4\">Experience</p>\n      <div className=\"mb-4\">\n        <div className=\"flex items-center gap-2 mb-2\">\n          <p className=\"text-lg text-neutral-600\">Cardiothoracic Surgeon, Hospital Name (2015-Present)</p>\n        </div>\n        <div className=\"flex items-center gap-2 mb-2\">\n          <p className=\"text-lg text-neutral-600\">Resident, Hospital Name (2012-2015)</p>\n        </div>\n      </div>\n    </section>\n    <section className=\"flex flex-col mb-12\">\n      <p className=\"text-3xl font-bold text-neutral-900 mb-4\">Publications</p>\n      <div className=\"mb-4\">\n        <div className=\"flex items-center gap-2 mb-2\">\n          <p className=\"text-lg text-neutral-600\">Doe J, et al. (2020). The effects of cardiothoracic surgery on patient outcomes. Journal of Cardiothoracic Surgery, 15(1), 1-8.</p>\n        </div>\n        <div className=\"flex items-center gap-2 mb-2\">\n          <p className=\"text-lg text-neutral-600\">Doe J, et al. (2019). The role of cardiothoracic surgery in the treatment of heart disease. Journal of Heart Disease, 10(2), 1-10.</p>\n        </div>\n      </div>\n    </section>\n    <section className=\"flex flex-col mb-12\">\n      <p className=\"text-3xl font-bold text-neutral-900 mb-4\">Contact Me</p>\n      <p className=\"text-lg text-neutral-600 leading-relaxed\">If you have any questions or would like to schedule an appointment, please don't hesitate to contact me.</p>\n      <div className=\"flex items-center gap-2 text-blue-600 hover:text-blue-800 transition-colors\">\n        <p className=\"text-lg text-neutral-600\">john.doe@example.com</p>\n      </div>\n    </section>\n  </main>\n  );\n}\n",
    "meta": {
        "provider": "groq",
        "model": "groq",
        "usage": {
            "queue_time": 0.054095664,
            "prompt_tokens": 1037,
            "prompt_time": 0.071126146,
            "completion_tokens": 2723,
            "completion_time": 4.569792085,
            "total_tokens": 3760,
            "total_time": 4.640918231
        }
    }
}