
```
                                 .@ 888S
                            ;@S8888:8%tX
 :XS.                 .;8: @8t88888t8888
X8%%S:              .8 8S888    :8.88S@:
8;8;888:        :@; 888888@8    88%888
%8:8%X8 t8. ;8 888.X8    88S@88888S %
 888S@@888  8@888@S8C    888    S%S:
 .@%888%@@t.888@@8@8@8::X88C   88 %
  ;S@X8@888S8X@@X8X88X888888%@888;
  Xt88X@8@@XX8S8X88@88888S888S.;
  t S888X8S8S8888X88@88%8@:@8%;
  :888X   @888    @88S88S888X
 .88;.     %X8    8@88S8X8:
 S8@S8@   8t8888%8@:8%S@88
 8%8;88888S@%.8S88;@8% %.
 :8.8    888    8XS:%:
 ::8St   88;   88S8;
   ;t 8X.8;%8 8%
```

# ocarina
Ocarina is a simple Python requests program for shouting at the [Majora](https://github.com/SamStudio8/majora) API.

## Configuration
On first run, `ocarina` will give you a command to generate the config file.
Edit the configuration and supply the three required parameters:

* `MAJORA_DOMAIN` the base URL of the Majora instance to send requests to
* `MAJORA_USER` your username on Majora
* `MAJORA_TOKEN` your API key, you can get this from your profile

Alternatively, you can specify `--env` and set these configuration parameters in your environment.

## Basic examples

### Add a biosample

```
ocarina put biosample --adm1 UK-WLS \
                  --central-sample-id "HOOT-OCARINA-012" \
                  --collection-date "2020-03-25" \
                  --source-age 29 \
                  --source-sex M
```

### Pool biosamples into a library

```
ocarina put library --library-name "BIRM-20200326-1844" \
                --library-seq-kit "LSK109" \
                --library-seq-protocol "LIGATION" \
                --library-layout-config "SINGLE" \
                --biosample HOOT-OCARINA-101 VIRAL_RNA PCR AMPLICON \
                --biosample HOOT-OCARINA-102 GENOMIC PCR AMPLICON
```

Or use a shortcut if all biosamples have the same library properties

```
ocarina put library --library-name "BIRM-20200326-1844" \
                --library-seq-kit "LSK109" \
                --library-seq-protocol "LIGATION" \
                --library-layout-config "SINGLE" \
                --biosamples HOOT-OCARINA-101 HOOT-OCARINA-102 \
                --apply-all-library VIRAL_RNA PCR AMPLICON
```

### Add a sequencing run for a library

```
ocarina put sequencing --library-name BIRM-20200326-1844 \
                   --sequencing-id "00000101-3fcb-421e-85e0-db5d48de28af" \
                   --instrument-make "OXFORD_NANOPORE" \
                   --instrument-model "GridION"
```
