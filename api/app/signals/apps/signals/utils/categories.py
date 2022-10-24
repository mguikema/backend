import argparse
import json
from django.utils.text import slugify

def parse_args():
    parser = argparse.ArgumentParser()
    optional = parser._action_groups.pop() 
    required = parser.add_argument_group('required arguments')
    required.add_argument('--json_file', required=True)
    parser._action_groups.append(optional)
    return parser.parse_args()

def json_categorie__to_fixtures(json_file):
    f = open(json_file, "r")
    categorie_data = json.loads(f.read())
    out = []
    i = 1
    for main in categorie_data:
        subs = main.get("onderwerpen")
        parentpk = i
        out.append({
            "model": "signals.category",
            "pk": i,
            "fields": {
                "parent": None,
                "slug": slugify(main.get("omschrijving")),
                "name": main.get("omschrijving"),
                "handling": "REST",
                "is_active": True,
                "departments": []
            }
        })
        for sub in subs:
            i += 1
            out.append({
                "model": "signals.category",
                "pk": i,
                "fields": {
                    "parent": parentpk,
                    "slug": slugify(sub.get("omschrijving")),
                    "name": sub.get("omschrijving"),
                    "handling": "REST",
                    "is_active": True,
                    "departments": []
                }
            })
            # print(sub.get("omschrijving"))
        i += 1
    json_out = json.dumps(out)
    print(json_out)
    with open("categries_fixtures.json", 'w') as outfile:
        json.dump(out, outfile)


if __name__ == '__main__':
    args = parse_args()
    print("Using args: {}".format(args))
    print(args.json_file)
    json_categorie__to_fixtures(args.json_file)